from typing import Any, Dict, List, Tuple, override

from ...framework import (
    Benchmark,
    DefaultAnalyzer,
    BenchmarkCategory,
    CircuitGenerator,
    CircuitSpec,
    DefaultBenchmarkExecutor,
    RunContext,
    ExecutionResult,
    AnalysisResult,
    BenchmarkResult,
    BenchmarkRegistry,
)
from ...framework import ProviderRegistry


class MQTBenchGenerator(CircuitGenerator):
    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:

        num_qubits = int(params["num_qubits"])
        provider = ProviderRegistry.get_provider("mqt_bench")
        if provider is None:
            raise ValueError("MQT Bench provider is not registered.")
        benchmark_name = self.context.benchmark_key.split("/")[-1]
        circuit = provider.get_circuit(benchmark_name, params)
        return [
            CircuitSpec(
                circuit=circuit,
                metadata={"benchmark": benchmark_name, "level": params["level"], "num_qubits": num_qubits},
            )
        ]


def _create_mqt_default_benchmark_class(bench_name: str) -> type:
    """Factory function to create a Benchmark class for a given MQT benchmark name."""
    class_name = f"MQTBench_{bench_name}_Benchmark"
    
    class MQTBenchmarkClass(Benchmark):
        origin = "core"
        source = "mqt_bench"
        name = bench_name
        generator = MQTBenchGenerator  # uses context.benchmark_key to extract the benchmark name
        executor = DefaultBenchmarkExecutor
        analyzer = DefaultAnalyzer
        supported_adapters: Tuple[str, ...] = ("mqss_qiskit",)
        category = BenchmarkCategory.SOFTWARE
        
        @override
        def validate_params(self, params: Dict[str, Any]) -> None:
            if not params:
                raise ValueError(f"Parameters must be provided for '{self.registry_key()}' benchmark.")
            required_params = ("num_qubits", "level")
            missing = [field for field in required_params if field not in params]
            if missing:
                raise ValueError(f"Missing required parameters for '{self.registry_key()}': {missing}")
            return None

    # Set a meaningful __name__ for better debugging and error messages
    MQTBenchmarkClass.__name__ = class_name
    MQTBenchmarkClass.__qualname__ = class_name
    MQTBenchmarkClass.__doc__ = f"Auto-registered MQT benchmark class for '{bench_name}'"
    
    return MQTBenchmarkClass


def auto_register_mqt_default_benchmarks():
    """Auto-register all available MQT benchmarks from the provider."""
    provider = ProviderRegistry.get_provider("mqt_bench")
    if provider is None:
        raise ValueError("MQT Bench provider is not registered.")
    
    available_benchmarks = provider.list_available()

    for bench_name in available_benchmarks:
        benchmark_cls = _create_mqt_default_benchmark_class(bench_name)
        BenchmarkRegistry.register_benchmark(benchmark_cls)


# Auto-register when module is imported
auto_register_mqt_default_benchmarks()