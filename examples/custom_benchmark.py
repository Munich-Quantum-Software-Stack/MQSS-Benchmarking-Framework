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
from mqssbench.runtime.benchmark_manager import BenchmarkManager
from mqssbench.cli.formatting import format_benchmark_result, format_registry_lists

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
        return AnalysisResult({
            "p_zero": p_zero,
        })


@BenchmarkRegistry.register_benchmark
class CustomBenchmark(Benchmark):
    origin = "user"
    source = "my_examples"
    name = "custom_benchmark"
    generator = CustomCircuitGenerator
    executor = DefaultBenchmarkExecutor
    analyzer = CustomAnalyzer
    supported_adapters: Tuple[str, ...] = ("mqss_qiskit",)
    category = BenchmarkCategory.SOFTWARE

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        if "num_qubits" not in params or "depth" not in params:
            raise ValueError("num_qubits and depth required")


if __name__ == "__main__":
    available_benchmarks = BenchmarkManager.get_available_benchmarks()
    print("===== Available benchmarks =====")
    print(format_registry_lists(benchmarks=available_benchmarks)) 

    config = {
        "benchmark": "user/my_examples/custom_benchmark",
        "adapter": "mqss_qiskit",
        "backend": "QExa20",
        "credentials": {"mqss_token": ""},
        "shots": 200,
        "benchmark_params": {"num_qubits": 1, "depth": 3},
    }

    manager = BenchmarkManager(config)
    result = manager.dispatch()

    print("===== Custom Benchmark Result =====")
    print(format_benchmark_result(result))
