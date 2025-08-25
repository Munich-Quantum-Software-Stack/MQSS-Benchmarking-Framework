from .base_handler import BenchmarkHandler
from circuits.hw_benchmark_circuits import get_hw_circuit_qiskit, get_hw_circuit_pennylane
from adapters.adapter_factory import get_adapter

class HardwareBenchmarkHandler(BenchmarkHandler):

    def __init__(self, config):
        super().__init__(config)

    def run(self):

        backend = get_adapter(self.config)

        # 2. Get the circuit function for the requested benchmark
        benchmark_name = self.config["benchmark_name"]
        circuit_fn = get_hw_circuit_qiskit(benchmark_name)

        # 3. Execute the circuit using the unified backend interface
        result = backend.run_circuit(circuit_fn, **self.config["params"])

        # 4. Return or log the result
        return {"benchmark": benchmark_name, "result": result}

    def build_circuits(self):
        
        benchmark_name = self.config["benchmark_name"]
        interface = self.config["interface"]
        circuit_fn = []
        if interface == "qiskit":
            circuit_fn = get_hw_circuit_qiskit(benchmark_name)

        elif interface == "pennylane":
            circuit_fn = get_hw_circuit_pennylane(benchmark_name)

        else:
            raise ValueError(f"Unsupported interface: {interface}")
        
        return circuit_fn
