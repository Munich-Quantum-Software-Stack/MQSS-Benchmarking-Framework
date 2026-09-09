from mqssbench.framework import (
    AdapterRegistry,
    DeviceAdapter,
    CircuitExecutionResult,
    ProfilingMetrics,
)


class ExampleAdapter(DeviceAdapter):

    name = "example_adapter"

    def __init__(self, adapter_params):

        self.adapter_params = adapter_params or {}
        self._backend_name = "example_backend"
        self._shots = int(self.adapter_params.get("shots", 1000))

    @classmethod
    def validate_profiling_config(cls, profiling_config):
        return

    def get_backend_name(self):

        return self._backend_name

    def execute_circuit(
        self,
        context,
        circuit,
        num_qubits=None,
        transpile_mode=True,
    ):

        shots = self._shots

        counts = {
            "0": int(shots * 0.8),
            "1": shots - int(shots * 0.8),
        }

        return CircuitExecutionResult(
            job_id="example-job",
            counts=counts,
            profiling_metrics=ProfilingMetrics(params={}),
            metadata={},
        )

def register() -> None:
    AdapterRegistry.register_adapter(ExampleAdapter)