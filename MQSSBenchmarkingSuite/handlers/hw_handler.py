from .base_handler import BenchmarkHandler
from ..benchmarks.registry import get_benchmark_class
from ..adapters.adapter_factory import get_adapter


class HardwareBenchmarkHandler(BenchmarkHandler):

    def __init__(self, config):
        super().__init__(config)

    def run(self):

        backend = get_adapter(self.config)

        # 1. Get benchmark config
        benchmark_name = self.config["benchmark_name"]
        interface = self.config.get("interface", "pennylane")
        benchmark_params = self.config.get("benchmark_params", {})

        # 2. Resolve benchmark class and run
        benchmark_class = get_benchmark_class(benchmark_name)
        benchmark_params = benchmark_class.validate_params(benchmark_params)
        benchmark_class.check_requirements(interface)
        runs = benchmark_class.execute(backend, benchmark_params)
        result = benchmark_class.analyze(benchmark_params, runs)

        # 4. Return or log the result
        return {"benchmark": benchmark_name, "result": result}

    def build_circuit(self):
        raise NotImplementedError("HW benchmarks circuit builder not implemented yet")
        # TODO: ADD RB as the first benchmark
