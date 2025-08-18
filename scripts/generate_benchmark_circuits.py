from manager import benchmark_manager

list_of_benchmarks = benchmark_manager.BenchmarkManager.get_available_benchmarks("HW")

config = {
    "benchmark_type": "HW",
    "benchmark_name": "RB",
    "interface": "pennylane",
    "backend": "QLM",
    "integrator": "MQSS",
    "credentials": {
        "mqss_token": "<TOKEN>"
    },
    "wires": 2,
    "params": {}
}

print("-----------------------------------------")
print("Available benchmarks:", list_of_benchmarks)
print("-----------------------------------------")
