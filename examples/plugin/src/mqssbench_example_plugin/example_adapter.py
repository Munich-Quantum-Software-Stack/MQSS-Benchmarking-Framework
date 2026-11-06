from mqssbench.framework import (
    AdapterRegistry,
    DeviceAdapter,
    ExecutionResult,
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

        # No real backend wired up for this example yet, so profiling values
        # are supplied manually rather than measured.
        profiling_params = {}
        if context.profiling and context.profiling.enabled:
            profiling_params = {
                "queue_time": 2.3,
                "quantum_execution": 0.85,
                "classical_execution": 0.12,
            }

        return ExecutionResult(
            job_id="example-job",
            counts=counts,
            profiling_metrics=ProfilingMetrics(params=profiling_params),
            metadata={},
        )

def register() -> None:
    AdapterRegistry.register_adapter(ExampleAdapter)