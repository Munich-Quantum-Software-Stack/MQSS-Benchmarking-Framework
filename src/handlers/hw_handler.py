from .base_handler import BenchmarkHandler
from circuits.hw_circuits import get_hw_circuit
from adapters.adapter_factory import get_adapter


class HardwareBenchmarkHandler(BenchmarkHandler):

    def __init__(self, config):
        super().__init__(config)

    def run(self):

        backend = get_adapter(self.config)

        # 1. Get benchmark config
        benchmark_name = self.config["benchmark_name"]
        interface = self.config.get("interface", "pennylane")
        params = self.config.get("params")

        # 2. Get the circuit function for the requested benchmark
        circuit_fn = get_hw_circuit(benchmark_name, interface)

        # 3. Execute the circuit using the unified backend interface
        result = backend.run_circuit(circuit_fn, **params)

        # 4. Return or log the result
        return {"benchmark": benchmark_name, "result": result}

        raise NotImplementedError("HW benchmarks run logic not implemented yet")

    def build_circuit(self):
        raise NotImplementedError("HW benchmarks circuit builder not implemented yet")
        # TODO: ADD RB as the first benchmark
