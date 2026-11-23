"""Small backend health benchmark based on a Bell-state circuit."""

from typing import Any, Dict, List, Tuple, override

from qiskit import QuantumCircuit

from ...framework import (
    AnalysisResult,
    Benchmark,
    BenchmarkAnalyzer,
    BenchmarkCategory,
    BenchmarkRegistry,
    CircuitGenerator,
    CircuitSpec,
    DefaultBenchmarkExecutor,
    RunContext,
)
from ...framework.types import CircuitExecutionResult


class HealthBenchmarkGenerator(CircuitGenerator):
    """Generate a two-qubit Bell-state circuit."""

    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:
        num_qubits = int(params.get("num_qubits", 2))
        if num_qubits != 2:
            raise ValueError("The health benchmark currently requires num_qubits=2.")

        circuit = QuantumCircuit(num_qubits, num_qubits)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure(range(num_qubits), range(num_qubits))
        return [CircuitSpec(circuit=circuit, metadata={"num_qubits": num_qubits})]


class HealthBenchmarkAnalyzer(BenchmarkAnalyzer):
    """Check that the backend executes the Bell-state circuit reliably."""

    @override
    def analyze(
        self, execution_results: List[CircuitExecutionResult], context: RunContext
    ) -> AnalysisResult:
        if len(execution_results) != 1:
            raise ValueError("Health benchmark expected exactly one execution result.")

        counts = execution_results[0].counts
        if not isinstance(counts, dict) or not counts:
            raise ValueError("Health benchmark received no measurement counts.")

        total_shots = sum(counts.values())
        if total_shots <= 0:
            raise ValueError("Health benchmark received zero measurement shots.")

        correlated_shots = counts.get("00", 0) + counts.get("11", 0)
        correlated_probability = correlated_shots / total_shots
        minimum_probability = float(
            context.params.get("min_correlated_probability", 0.8)
        )
        if not 0 <= minimum_probability <= 1:
            raise ValueError(
                "min_correlated_probability must be between 0 and 1."
            )

        if correlated_probability < minimum_probability:
            raise RuntimeError(
                "Health benchmark failed: correlated Bell-state probability "
                f"{correlated_probability:.3f} is below the required "
                f"{minimum_probability:.3f}."
            )

        return AnalysisResult(
            metrics={
                "healthy": True,
                "total_shots": total_shots,
                "correlated_shots": correlated_shots,
                "correlated_probability": correlated_probability,
                "minimum_correlated_probability": minimum_probability,
            }
        )


class HealthBenchmark(Benchmark):
    """Quick smoke test for backend availability and basic execution quality."""

    origin = "core"
    source = "native"
    name = "health"
    generator = HealthBenchmarkGenerator
    executor = DefaultBenchmarkExecutor
    analyzer = HealthBenchmarkAnalyzer
    supported_adapters: Tuple[str, ...] = ("mqss_qiskit", "qiskit_simulator")
    category = BenchmarkCategory.HARDWARE

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        if "num_qubits" in params and int(params["num_qubits"]) != 2:
            raise ValueError("The health benchmark currently requires num_qubits=2.")
        if "min_correlated_probability" in params:
            threshold = float(params["min_correlated_probability"])
            if not 0 <= threshold <= 1:
                raise ValueError(
                    "min_correlated_probability must be between 0 and 1."
                )


def register() -> None:
    """Plugin registration hook."""
    BenchmarkRegistry.register_benchmark(HealthBenchmark)
