from mqssbench.runtime.benchmark_manager import BenchmarkManager
from mqssbench.cli.formatting import format_benchmark_result, format_registry_lists

# Show all benchmarks that the registry discovered
print("\n===== Available Benchmarks =====")
print(format_registry_lists(benchmarks=BenchmarkManager.get_available_benchmarks())) 

# Example config — users can replace with their own YAML file
config = {
    "benchmark": "core/native/quantum_volume",
    "adapter": "mqss_qiskit",
    "backend": "QExa20",
    "credentials": {"mqss_token": ""},
    "shots": 200,
    "benchmark_params": {
        "num_qubits": 3,
        "depth": 3,
        "trials": 2
    },
    "metrics": [
        "fidelity",
        "time-to-solution",
        "compile-time",
        "gate-count",
        "classical-compute-time",
    ],
}

manager = BenchmarkManager(config)
result = manager.dispatch()

print("\n===== Benchmark Result =====")
print(format_benchmark_result(result))
