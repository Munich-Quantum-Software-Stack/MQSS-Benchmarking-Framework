from typing import Any, Dict, List, Tuple, override

from qiskit import QuantumCircuit

from mqssbench.framework import (
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

from . import PLUGIN_ORIGIN

class CustomCircuitGenerator(CircuitGenerator):
    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:
        num_qubits = int(params["num_qubits"])
        depth = int(params["depth"])
        qc = QuantumCircuit(num_qubits)
        for _ in range(depth):
            qc.h(0)
            qc.x(0)
        qc.measure_all()
        return [
            CircuitSpec(
                circuit=qc,
                metadata={"num_qubits": num_qubits, "depth": depth},
            )
        ]


class CustomAnalyzer(BenchmarkAnalyzer):
    @override
    def analyze(self, execution_results: List[ExecutionResult], context: RunContext) -> AnalysisResult:
        result = execution_results[0]
        counts = result.counts
        total = sum(counts.values())
        p_zero = counts.get("0", 0) / total if total > 0 else 0.0
        return AnalysisResult(
            metrics={
                "p_zero": p_zero,
            },
            artifacts={},
        )


class ExampleBenchmark(Benchmark):
    origin = PLUGIN_ORIGIN
    source = "native"
    name = "example_benchmark"
    generator = CustomCircuitGenerator
    executor = DefaultBenchmarkExecutor
    analyzer = CustomAnalyzer
    supported_adapters: Tuple[str, ...] = ("example_adapter", "mqss_qiskit")
    category = BenchmarkCategory.SOFTWARE

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        if "num_qubits" not in params or "depth" not in params:
            raise ValueError("num_qubits and depth required")


def register() -> None:
    BenchmarkRegistry.register_benchmark(ExampleBenchmark)