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
        if edges[0] >= num_qubits or edges[1] >= num_qubits:
            raise ValueError("QAOA Benchmark analysis failed: edge index out of range.")

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


def maxcut_expectation(bitstring: str, edges: list[tuple[int, int]]) -> float:
    """
    Calculate the MaxCut expectation value for a given bitstring and edge list.
    Each edge contributes +1 if the bits are different, 0 otherwise.
    """
    value = 0
    for i, j in edges:
        if bitstring[i] != bitstring[j]:
            value += 1
    return value


class QAOAAnalyzer(BenchmarkAnalyzer):
    @override
    def analyze(
        self, execution_results: List[ExecutionResult], context: RunContext
    ) -> AnalysisResult:
        # num_qubits = int(context.params["num_qubits"])
        edges = list(context.params["edges"])
        exp_value = 0.0
        for result in execution_results:
            counts = result.counts

            total = sum(counts.values())
            if total == 0:
                raise ValueError(
                    "QAOA Benchmark analysis failed: zero total counts encountered."
                )
            exp_value = maxcut_expectation(counts, edges)
        return AnalysisResult(
            metrics={"exp_value": exp_value},
        )


@BenchmarkRegistry.register_benchmark
class QAOABenchmark(Benchmark):
    origin = "core"
    source = "native"
    name = "qaoa"
    generator = QAOAGenerator
    executor = HybridBenchmarkExecutor
    analyzer = QAOAAnalyzer
    supported_adapters: Tuple[str, ...] = ("mqss_qiskit",)
    category = BenchmarkCategory.HARDWARE

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
