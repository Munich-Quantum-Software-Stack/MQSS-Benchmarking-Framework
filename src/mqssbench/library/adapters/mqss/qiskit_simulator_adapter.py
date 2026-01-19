import logging
from typing import override
from qiskit import QuantumCircuit
from qiskit_aer.primitives import SamplerV2
from ....framework.adapter import DeviceAdapter
from ....framework.adapter_registry import AdapterRegistry
from ....framework.types import (
    ProfilingConfig,
    RunContext,
    ProfilingMetrics,
    ExecutionResult,
)

logger = logging.getLogger(__name__)


@AdapterRegistry.register_adapter
class QiskitSimulatorAdapter(DeviceAdapter):
    name = "qiskit_simulator"

    def __init__(self, config):
        self.config = config
        self._backend_name = "qiskit_simulator"
        if not isinstance(config, dict):
            raise TypeError("config must be a dict")

        self._shots = int(config["shots"]) if config.get("shots") is not None else 1024
        # Adapter and backend will be created lazily in _get_backend()

    def _get_backend(self):

        self._backend = SamplerV2()
        return self._backend

    @override
    def get_backend_name(self) -> str:
        """Return the backend name."""
        return self._backend_name

    @override
    @classmethod
    def validate_profiling_config(cls, profiling_config: ProfilingConfig):
        """Validate profiling parameters."""
        if profiling_config is None:
            return

    @override
    def execute_circuit(
        self, context: RunContext, circuit, num_qubits=None, transpile_mode=True
    ) -> ExecutionResult:
        """Given a Qiskit circuit, run it using the Qiskit Simulator Adapter

        Args:
            context (RunContext): The run context containing execution metadata.
            circuit (callable): A builder function returning a `QuantumCircuit`.
            num_qubits: number of qubits for device creation. Defaults to None.

        Returns:
            ExecutionResult: Result from executing the circuit.
        """
        # Build circuit
        if callable(circuit):
            built_circuit = circuit()
        else:
            built_circuit = circuit

        # print(f"Running circuit on backend {self._backend_name} ...")
        # print("circuit", built_circuit)

        if not isinstance(built_circuit, QuantumCircuit):
            raise TypeError("circuit must be a Qiskit QuantumCircuit")

        backend = self._get_backend()
        if self._shots is not None:
            job = backend.run([built_circuit], shots=self._shots)
        else:
            job = backend.run([built_circuit])

        result = job.result()
        counts = result[0].data.c.get_counts()

        job_id = job.job_id()

        return ExecutionResult(
            job_id=job_id,
            counts=counts,
            profiling_metrics=ProfilingMetrics(params=None),
        )
