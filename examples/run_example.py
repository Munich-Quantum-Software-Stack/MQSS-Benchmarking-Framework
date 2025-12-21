from mqssbench.runtime.benchmark_manager import BenchmarkManager
from mqssbench.cli.formatting import format_benchmark_result, format_registry_lists

# Show all benchmarks that the registry discovered
print("\n===== Available Benchmarks =====")
print(format_registry_lists(benchmarks=BenchmarkManager.get_available_benchmarks())) 

# Example config — users can replace with their own YAML file
config = {
    "benchmark": "core/native/quantum_volume",
    "benchmark_params": {
        "num_qubits": 3,
        "depth": 3,
        "trials": 2
    },
    "adapter": "mqss_qiskit",
    "backend": "QExa20",
    "credentials": {"mqss_token": ""},
    "shots": 200,
    "output_dir": "./results",
    "storage": {
        "type": "file",
        "file": {
            "format": "json"
        }
    }
}

manager = BenchmarkManager(config)
results = manager.dispatch()

print("\n===== Benchmark Result =====")
for r in results:
    print(format_benchmark_result(r))
    print()  # blank line between runs