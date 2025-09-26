
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
config = {
    "benchmark_type": "SW",
    "benchmark_name": "VQE-H2",
    "interface": "pennylane",
    "backend": MQSS_BACKEND,
    "credentials": {"mqss_token": MQSS_TOKEN},
    "wires": 2,
    "params": {"depth": 100},
    "metrics": metrics,
}

benchmark_manager = BenchmarkManager(config)
benchmark_manager.dispatch()
