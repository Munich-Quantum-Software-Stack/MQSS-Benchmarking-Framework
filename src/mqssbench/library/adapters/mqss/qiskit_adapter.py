import logging
from typing import override
from qiskit import QuantumCircuit
from qiskit import transpile
from ....framework.adapter import DeviceAdapter
from mqss.qiskit_adapter import MQSSQiskitAdapter
from ....framework.adapter_registry import AdapterRegistry
from ....framework.types import (
    ProfilingConfig,
    RunContext,
    ProfilingMetrics,
    ExecutionResult,
)
from .config import MQSS_TOKEN, MQSS_BACKEND, MQSS_VALID_PROFILING_METRICS

logger = logging.getLogger(__name__)

MQSS_QISKIT_PROFILING_ENABLED = True


class QiskitAdapter(DeviceAdapter):
    name = "mqss_qiskit"

    def __init__(self, adapter_params):
        self.adapter_params = adapter_params

        if not isinstance(adapter_params, dict):
            raise TypeError("adapter_params must be a dict")

        self._backend_name = str(adapter_params.get("backend", "")).strip()
        if self._backend_name is None or self._backend_name == "":
            self._backend_name = (MQSS_BACKEND).strip()
        if not self._backend_name:
            raise ValueError("Missing required config: backend or MQSS_BACKEND")

        credentials = adapter_params.get("credentials") or {}
        self._token = str(
            credentials.get("mqss_token") if isinstance(credentials, dict) else None
        ).strip()
        if self._token is None or self._token == "":
            self._token = (MQSS_TOKEN).strip()
        if not self._token:
            raise ValueError(
                "Missing required config: credentials.mqss_token or MQSS_TOKEN"
            )

        self._shots = int(adapter_params.get("shots")) if adapter_params.get("shots") is not None else None
        backend_params = adapter_params.get("backend_params") or {}
        if not isinstance(backend_params, dict):
            raise TypeError("adapter_params.backend_params must be a dict")
        self._backend_params = dict(backend_params)
        # Adapter and backend will be created lazily in _get_backend()

    def _get_backend(self):
        """Lazy creation of backend."""
        if not hasattr(self, "_adapter"):
            self._adapter = MQSSQiskitAdapter(token=self._token)
        if not hasattr(self, "_backend"):
            self._backend = self._adapter.get_backend(self._backend_name)
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
        if profiling_config.enabled and not MQSS_QISKIT_PROFILING_ENABLED:
            raise ValueError(f"Profiling is no available in {cls.name}.")
        if (
            not profiling_config.metrics
        ):  # null or empty means all metrics are requested
            return
        invalid_metrics = set(profiling_config.metrics) - MQSS_VALID_PROFILING_METRICS
        if invalid_metrics:
            raise ValueError(
                f"Invalid profiling metrics for {cls.name}: {invalid_metrics}. "
                f"Valid metrics are: {MQSS_VALID_PROFILING_METRICS}"
            )

    @override
    def execute_circuit(
        self, context: RunContext, circuit, num_qubits=None, transpile_mode=True
    ) -> ExecutionResult:
        """Given a Qiskit circuit, run it using the QiskitAdapter

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

        print(f"Running circuit on backend {self._backend_name} ...")
        logger.info("circuit\n%s", built_circuit)

        if not isinstance(built_circuit, QuantumCircuit):
            raise TypeError("circuit must be a Qiskit QuantumCircuit")

        backend = self._get_backend()
        # Transpile for this backend so the basis matches what the device supports
        if transpile_mode is True:
            transpiled_circuit = transpile(
                built_circuit,
                backend=backend,
                optimization_level=0,
            )
        else:
            transpiled_circuit = built_circuit
        backend_params = dict(self._backend_params)
        if self._shots is not None:
            job = backend.run(transpiled_circuit, shots=self._shots, **backend_params)
        else:
            job = backend.run(transpiled_circuit, **backend_params)
        job_id = job.job_id()
        job_result = job.result()
        counts = job_result.get_counts()
        if MQSS_QISKIT_PROFILING_ENABLED:
            profiling_data = getattr(job_result, "job_profiler_metrics", None)
        else:
            profiling_data = None
        return ExecutionResult(
            job_id=job_id,
            counts=counts,
            profiling_metrics=ProfilingMetrics(params=profiling_data),
        )


def register() -> None:
    """Plugin registration hook."""
    AdapterRegistry.register_adapter(QiskitAdapter)