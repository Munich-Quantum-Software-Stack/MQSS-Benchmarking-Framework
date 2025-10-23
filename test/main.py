# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from MQSSBenchmarkingSuite.manager.benchmark_manager import BenchmarkManager
from MQSSBenchmarkingSuite.adapters.config import MQSS_TOKEN, MQSS_BACKEND

list_of_benchmarks = BenchmarkManager.get_available_benchmarks()

metrics = [
    "fidelity",
    "time-to-solution",
    "compile-time",
    "gate-count",
    "classical-compute-time",
]

sample_config_sw_vqe = {
    "benchmark_type": "SW",
    "benchmark_name": "vqe_su2",
    "interface": "qiskit",
    "backend": MQSS_BACKEND,
    "credentials": {"mqss_token": MQSS_TOKEN},
    "params": {},
    "benchmark_params": {
        "num_qubits": 2,
    },
    "metrics": metrics,
}

sample_config_hw_rb = {
    "benchmark_type": "HW",
    "benchmark_name": "randomized_benchmarking",
    "interface": "qiskit",
    "backend": "QExa20",
    "credentials": {"mqss_token": MQSS_TOKEN},
    "shots": 200,
    "params": {},
    "benchmark_params": {
        "num_qubits": 2,
        "lengths": [2, 4, 8, 16],
        "num_sequences": 2
    },
    "metrics": metrics,
}

sample_config_hw_qv = {
    "benchmark_type": "HW",
    "benchmark_name": "quantum_volume", 
    "interface": "qiskit",
    "backend": "QExa20",
    "credentials": {"mqss_token": MQSS_TOKEN},
    "shots": 200,
    "params": {},
    "benchmark_params": {
        "num_qubits": 2,
        "depth": 2,
        "trials": 2
    },
    "metrics": metrics,
}

benchmark_manager = BenchmarkManager(sample_config_sw_vqe)
print("Available benchmarks:", benchmark_manager.get_available_benchmarks())
result = benchmark_manager.dispatch()
print(result)