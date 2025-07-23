from handlers import HardwareBenchmarkHandler
from handlers import SoftwareBenchmarkHandler


class BenchmarkManager:

    def get_available_benchmarks():
        return ["randomized_benchmarking", "to", "be", "filled"]

    def __init__(self, config: dict):
        self.config = config

    def dispatch(self):
        benchmark_type = self.config["benchmark_type"]
        if benchmark_type == "HW":
            handler = HardwareBenchmarkHandler(self.config)
        elif benchmark_type == "SW":
            handler = SoftwareBenchmarkHandler(self.config)
        elif benchmark_type == "Algorithm":
            raise NotImplementedError(
                "Algorithmic benchmark builder not implemented yet"
            )
        elif benchmark_type == "Simulator":
            raise NotImplementedError("Simulator benchmark builder not implemented yet")
        else:
            raise ValueError(f"Unsupported benchmark type: {benchmark_type}")
        return handler.run()
