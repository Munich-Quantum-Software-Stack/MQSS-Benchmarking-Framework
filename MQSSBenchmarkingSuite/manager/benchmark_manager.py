from ..handlers import HardwareBenchmarkHandler
from ..handlers import SoftwareBenchmarkHandler
from ..benchmarks.registry import list_registerd_benchmarks


class BenchmarkManager:

    @staticmethod
    def get_available_benchmarks(): 
        # TODO: consider this part when implementing the unified approach to load external benchmarks (e.g. mqtbench or even custom ones)
        return list_registerd_benchmarks()

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

    # TODO: consider adding a method here to check if the config is valid, e.g. num_qubits should be provided
