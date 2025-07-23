import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.manager.benchmark_manager import BenchmarkManager

list_of_benchmarks = BenchmarkManager.get_available_benchmarks()

config = {
    "benchmark_type": "HW",
    "benchmark_name": list_of_benchmarks[0],
    "interface": "pennylane",
    "backend": "QLM",
    "credentials": {
        "mqss_token": "ADlkrgLcbt0jUHUYz4Er2ouzvWATOCNx2ntnWJ1OJlajm2r1J2BqJXBtpgJcBd3l"
    },
    "wires": 2,
    "params": {"depth": 100},
}

benchmark_manager = BenchmarkManager(config)
benchmark_manager.dispatch()
