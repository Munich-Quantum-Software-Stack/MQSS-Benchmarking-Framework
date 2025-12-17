from typing import Any, Dict, List, Tuple, override
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit

from ...framework.utils import make_output_path, safe_plot_show
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


class GHZGenerator(CircuitGenerator):
    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:

        num_qubits = int(params["num_qubits"])

        circuits: List[CircuitSpec] = []
        seed = 42

        circuit = QuantumCircuit(num_qubits, num_qubits)
        circuit.h(0)
        for i in range(1, num_qubits):
            circuit.cx(0, i)
        circuit.measure_all()
        circuits.append(
            CircuitSpec(
                circuit=circuit,
                metadata={
                    "num_qubits": num_qubits,
                    "seed": seed,
                },
            )
        )
        return circuits


class GHZAnalyzer(BenchmarkAnalyzer):
    @override
    def analyze(
        self, execution_results: List[ExecutionResult], context: RunContext
    ) -> AnalysisResult:
        num_qubits = int(context.params["num_qubits"])
        zero_state = "0" * num_qubits
        one_state = "1" * num_qubits
        ghz_counts = {zero_state: 0, one_state: 0}
        total = 0

        # Sum counts for GHZ states across all execution results
        for result in execution_results:
            counts = result.counts
            for bitstring, count in counts.items():
                # Only consider the last num_qubits bits
                bits = bitstring[-num_qubits:]
                if bits == zero_state:
                    ghz_counts[zero_state] += count
                elif bits == one_state:
                    ghz_counts[one_state] += count
                total += count

        # Calculate populations (probabilities)
        populations = {
            zero_state: ghz_counts[zero_state] / total if total else 0.0,
            one_state: ghz_counts[one_state] / total if total else 0.0,
        }

        # Store for plotting
        self._ghz_populations = populations
        self._ghz_total = total
        self._ghz_num_qubits = num_qubits
        self._plot(
            lengths=[0],  # Dummy lengths for compatibility
            survivals=[populations[zero_state] + populations[one_state]],
            context=context,
        )
        return AnalysisResult(results={"ghz_populations": populations, "total": total})

    def _plot(
        self, lengths: List[int], survivals: List[float], context: RunContext
    ) -> None:
        # Use stored populations from analyze
        populations = getattr(self, "_ghz_populations", None)
        total = getattr(self, "_ghz_total", None)
        num_qubits = getattr(self, "_ghz_num_qubits", None)
        if populations is None or total is None or num_qubits is None:
            print("No GHZ populations to plot.")
            return

        states = ["0" * num_qubits, "1" * num_qubits]
        sim_values = [populations[states[0]], populations[states[1]]]
        ideal_value = 0.5  # For perfect GHZ, each state has 50% probability

        backend_name = context.adapter.get_backend_name()
        plt.figure(figsize=(6, 5))
        if backend_name:
            plt.title(f"GHZ State Population on {backend_name}")
        else:
            plt.title("GHZ State Population")
        plt.ylabel("Population Fraction")
        plt.ylim(0, 1)

        # Plot ideal (shadow) bars
        plt.bar(
            states,
            [ideal_value, ideal_value],
            color="#cccccc",
            alpha=0.5,
            label="Ideal (Simulated)",
        )
        # Plot simulation results
        plt.bar(
            states,
            sim_values,
            color=["#1f77b4", "#ff7f0e"],
            alpha=0.8,
            label="Simulation",
        )

        for i, val in enumerate(sim_values):
            plt.text(i, val + 0.02, f"{val:.2f}", ha="center", va="bottom", fontsize=10)

        plt.legend()
        plt.grid(axis="y", linestyle=":", alpha=0.7)

        if context.output_config.save:
            bench_name = context.benchmark_key.split("/")[-1]
            filename = make_output_path(
                name=bench_name,
                output_dir=context.output_config.output_dir,
                is_plot=True,
            )
            plt.savefig(filename)

        safe_plot_show()


@BenchmarkRegistry.register_benchmark
class GHZ(Benchmark):
    origin = "core"
    source = "native"
    name = "ghz"
    generator = GHZGenerator
    executor = DefaultBenchmarkExecutor
    analyzer = GHZAnalyzer
    supported_adapters: Tuple[str, ...] = ("mqss_qiskit",)
    category = BenchmarkCategory.HARDWARE

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        if not params:
            raise ValueError(
                f"Parameters must be provided for '{self.registry_key()}' benchmark."
            )
        required_params = ["num_qubits"]
        missing = [field for field in required_params if field not in params]
        if missing:
            raise ValueError(
                f"Missing required parameters for '{self.registry_key()}': {missing}"
            )
