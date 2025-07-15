from .base_handler import BenchmarkHandler
from adapters.adapter_factory import get_adapter
from circuits.sw_benchmark_circuits import get_sw_benchmark_by_name


class SoftwareBenchmarkHandler(BenchmarkHandler):
    def run(self):

        backend = get_adapter(self.config)

        name = self.config["benchmark_name"]
        num_qubits = self.config["benchmark_name"]
        # TODO: Indicate which modules have to be benchmarked through the config
        circuit_fn = get_sw_benchmark_by_name(name, num_qubits)

        result = backend.run_circuit(circuit_fn, **self.config["params"])

        return {"benchmark": name, "result": result}

        raise NotImplementedError("SW benchmarks run logic not implemented yet")
        # TODO: Check what needs to be implemented by the MQSS modules

    def build_circuit(self):
        raise NotImplementedError("SW benchmarks circuit builder not implemented yet")
        # TODO: Use MQTBench here
