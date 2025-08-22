from manager import benchmark_manager as bm

config = {
    "benchmark_type": "HW",
    "benchmark_name": "RB",
    "interface": "qiskit",
    "backend": "QLM",
    "integrator": "MQSS",
    "credentials": {
        "mqss_token": "<TOKEN>"
    },
    "num_qubits": 2,
    "params": {}
}

# Test avaiable benchmarks
# available_benchmarks = bm.BenchmarkManager.get_available_benchmarks("HW")
# print("-----------------------------------------")
# print("Available benchmarks:", available_benchmarks)
# print("-----------------------------------------")

# Test class benchmark manager and generate circuits
benchmark_manager = bm.BenchmarkManager(config)
list_of_hw_bench_circuits = benchmark_manager.generate_benchmark_circuits()
print(list_of_hw_bench_circuits)

