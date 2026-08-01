from collections import defaultdict
from typing import Any, Dict, List, Tuple, override
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from ...framework.utils import make_output_filepath
from ...framework import (
    Benchmark,
    BenchmarkAnalyzer,
    BenchmarkCategory,
    CircuitGenerator,
    CircuitSpec,
    DefaultBenchmarkExecutor,
    RunContext,
    ExecutionResult,
    AnalysisResult,
    BenchmarkRegistry,
)


class RandomizedBenchmarkingGenerator(CircuitGenerator):
    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:
        from qiskit_experiments.library.randomized_benchmarking import StandardRB

        num_qubits = int(params["num_qubits"])
        lengths = list(params["lengths"])
        num_sequences = int(params["num_sequences"])
        circuits: List[CircuitSpec] = []
        seed = 42

        experiment = StandardRB(
            physical_qubits=list(range(num_qubits)),
            lengths=lengths,  # all lengths at once
            num_samples=num_sequences,
            seed=seed,
        )

        n_lengths = len(lengths)
        for idx, circ in enumerate(experiment.circuits()):
            seq_idx = idx // n_lengths  # compute sequence index
            length = circ.metadata["xval"]  # Qiskit stores the length in metadata
            circuits.append(
                CircuitSpec(
                    circuit=circ,
                    metadata={
                        "num_qubits": num_qubits,
                        "length": length,
                        "num_sequences": num_sequences,
                        "sequence_index": seq_idx,
                        "seed": seed,
                    },
                )
            )

        return circuits


class RandomizedBenchmarkingAnalyzer(BenchmarkAnalyzer):
    @override
    def analyze(
        self, execution_results: List[ExecutionResult], context: RunContext
    ) -> AnalysisResult:
        num_qubits = int(context.params["num_qubits"])
        zero_state = "0" * num_qubits
        grouped_survivals: Dict[int, List[float]] = defaultdict(list)

        for result in execution_results:
            counts = result.counts
            length = int(result.metadata["length"])
            total = sum(counts.values())
            if total == 0:
                raise ValueError(
                    "Randomized Benchmarking analysis failed: zero total counts encountered."
                )
            survival = counts.get(zero_state, 0) / total
            grouped_survivals[length].append(float(survival))

        if not grouped_survivals:
            raise ValueError(
                "Randomized Benchmarking analysis failed: no survival data found."
            )

        lengths = sorted(grouped_survivals.keys())
        mean_survivals = [
            float(np.mean(grouped_survivals[length])) for length in lengths
        ]

        def decay_model(clifford_lengths, amp, depolarizing, offset):
            return amp * (depolarizing**clifford_lengths) + offset

        Ls = np.array(lengths, dtype=float)
        ys = np.array(mean_survivals, dtype=float)
        popt, _ = curve_fit(
            decay_model,
            Ls,
            ys,
            p0=[0.5, 0.95, 0.5],
            bounds=([-1, 0, -1], [2, 1, 2]),
        )
        _, p_decay, _ = popt
        dimension = 2**num_qubits
        avg_gate_error = ((dimension - 1) / dimension) * (1 - float(p_decay))

        artifacts = {}
        if context.report_config.analysis.visualization.enabled:
            plot_filename = self._plot(lengths, mean_survivals, context)
            artifacts["decay_plot"] = plot_filename

        return AnalysisResult(
            metrics={
                "mean_survivals": mean_survivals,
                "decay_p": float(p_decay),
                "avg_gate_error": float(avg_gate_error),
            },
            artifacts=artifacts,
        )

    def _plot(
        self, lengths: List[int], survivals: List[float], context: RunContext
    ) -> None:
        backend_name = context.adapter.get_backend_name()
        plt.figure()
        if backend_name:
            plt.title(f"Randomized Benchmarking on {backend_name}")
        else:
            plt.title("Randomized Benchmarking")
        plt.xlabel("Clifford Length")
        plt.ylabel("Mean Survival Probability")
        plt.grid(True)
        plt.xticks(lengths)
        plt.plot(lengths, survivals, marker="o", linestyle="-")

        filename = make_output_filepath(
            context.benchmark_key, context.run_dir, tag="decay_plot"
        )
        plt.savefig(filename)

        return filename


class RandomizedBenchmarkingBenchmark(Benchmark):
    origin = "core"
    source = "native"
    name = "randomized_benchmarking"
    generator = RandomizedBenchmarkingGenerator
    executor = DefaultBenchmarkExecutor
    analyzer = RandomizedBenchmarkingAnalyzer
    supported_adapters: Tuple[str, ...] = ("mqss_qiskit", "qiskit_simulator")
    category = BenchmarkCategory.HARDWARE

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        if not params:
            raise ValueError(
                f"Parameters must be provided for '{self.registry_key()}' benchmark."
            )
        required_params = ["num_qubits", "lengths", "num_sequences"]
        missing = [field for field in required_params if field not in params]
        if missing:
            raise ValueError(
                f"Missing required parameters for '{self.registry_key()}': {missing}"
            )


def register() -> None:
    """Plugin registration hook."""
    BenchmarkRegistry.register_benchmark(RandomizedBenchmarkingBenchmark)