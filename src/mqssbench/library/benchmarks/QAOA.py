from typing import Any, Dict, List, Tuple, override


from ...framework import (
    Benchmark,
    BenchmarkAnalyzer,
    BenchmarkCategory,
    CircuitGenerator,
    CircuitSpec,
    HybridBenchmarkExecutor,
    RunContext,
    ExecutionResult,
    AnalysisResult,
    BenchmarkRegistry,
)
from qiskit import QuantumCircuit

import matplotlib.pyplot as plt
from ...framework.utils import make_output_filepath


class QAOAGenerator(CircuitGenerator):
    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:

        num_qubits = int(params["num_qubits"])
        edges = list(params["edges"])
        parameters = list(params["parameters"])
        gammas = parameters[0::2]
        betas = parameters[1::2]
        # gammas = list(params["gammas"])
        # betas = list(params["betas"])

        circuits: List[CircuitSpec] = []
        if len(gammas) != len(betas):
            raise ValueError(
                "QAOA Benchmark generation failed: number of gammas and betas must be equal."
            )
        if len(gammas) == 0 or len(betas) == 0:
            raise ValueError(
                "QAOA Benchmark generation failed: at least one gamma and one beta must be provided."
            )
        for edge in edges:
            if edge[0] >= num_qubits or edge[1] >= num_qubits:
                raise ValueError(
                    "QAOA Benchmark analysis failed: edge index out of range."
                )
        if len(edges) <= 0:
            raise ValueError(
                "QAOA Benchmark analysis failed: at least one edge must be provided."
            )

        def U_B_qiskit(qc, beta, num_qubits):
            for wire in range(num_qubits):
                qc.rx(2 * beta, wire)

        def U_C_qiskit(qc, gamma, edges):
            for edge in edges:
                qc.cx(edge[0], edge[1])
                qc.rz(gamma, edge[1])
                qc.cx(edge[0], edge[1])

        qc = QuantumCircuit(num_qubits, num_qubits)
        # Apply Hadamards to get the n-qubit |+> state
        for qubit in range(num_qubits):
            qc.h(qubit)
        # p instances of unitary operators
        for gamma, beta in zip(gammas, betas):
            U_C_qiskit(qc, gamma, edges)
            U_B_qiskit(qc, beta, num_qubits)
        # Measurement
        qc.measure(range(num_qubits), range(num_qubits))

        circuits.append(
            CircuitSpec(
                circuit=qc,
                metadata={
                    "num_qubits": num_qubits,
                    "edges": edges,
                    "parameters": parameters,
                },
            )
        )

        return circuits


def maxcut_expectation(counts: dict, edges: list[tuple[int, int]]) -> float:
    """
    Calculate the MaxCut expectation value for a given bitstring and edge list.
    Each edge contributes +1 if the bits are different, 0 otherwise.
    """
    value = 0
    for bitstring, count in counts.items():
        for i, j in edges:
            if bitstring[i] != bitstring[j]:
                value += count
            # else:
            #     value -= count
    value /= sum(counts.values())
    return value


class QAOAAnalyzer(BenchmarkAnalyzer):
    @override
    def analyze(
        self, execution_results: List[ExecutionResult], context: RunContext
    ) -> AnalysisResult:

        for result in execution_results:
            counts = result.counts

            total = sum(counts.values())
            if total == 0:
                raise ValueError(
                    "QAOA Benchmark analysis failed: zero total counts encountered."
                )

        artifacts = {}
        if context.report_config.analysis.visualization.enabled:
            plot_filename = self._plot(execution_results[-1].counts, context)
            artifacts["decay_plot"] = plot_filename

        return AnalysisResult(
            metrics={
                "exp_value": execution_results[-1].exp_value,
                "optimal_parameters": execution_results[-1].optimal_params,
            },
            artifacts=artifacts,
        )

    def _plot(self, counts: dict, context: RunContext) -> str:
        backend_name = context.adapter.get_backend_name()
        plt.figure()
        if backend_name:
            plt.title(
                f"QAOA on {backend_name} with {context.params['num_qubits']} qubits"
            )
        else:
            plt.title(f"QAOA with {context.params['num_qubits']} qubits")
        plt.xlabel("Bitstrings")
        plt.ylabel("Probability")

        # plt.xticks(list(counts.keys()), rotation="vertical")
        plt.xticks(rotation=45, ha="right")
        plt.bar(list(counts.keys()), list(counts.values()))

        filename = make_output_filepath(
            context.benchmark_key, context.run_dir, tag="decay_plot"
        )
        plt.savefig(filename)

        return filename


class QAOABenchmark(Benchmark):
    origin = "core"
    source = "native"
    name = "qaoa"
    generator = QAOAGenerator
    executor = HybridBenchmarkExecutor
    analyzer = QAOAAnalyzer
    supported_adapters: Tuple[str, ...] = ("mqss_qiskit", "qiskit_simulator")
    category = BenchmarkCategory.ALGORITHM

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        if not params:
            raise ValueError(
                f"Parameters must be provided for '{self.registry_key()}' benchmark."
            )
        required_params = ["num_qubits", "edges", "parameters"]
        missing = [field for field in required_params if field not in params]
        if missing:
            raise ValueError(
                f"Missing required parameters for '{self.registry_key()}': {missing}"
            )


def register() -> None:
    """Plugin registration hook."""
    BenchmarkRegistry.register_benchmark(QAOABenchmark)