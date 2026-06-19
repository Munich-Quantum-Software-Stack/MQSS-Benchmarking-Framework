import logging
from typing import override, Callable, cast
from mqss.pennylane_adapter.device import MQSSPennylaneDevice
from pennylane import QNode
from ....framework.adapter import DeviceAdapter
from ....framework.adapter_registry import AdapterRegistry
from .config import MQSS_TOKEN, MQSS_BACKEND, MQSS_VALID_PROFILING_METRICS
from ....framework.types import ProfilingConfig, RunContext, ProfilingMetrics, ExecutionResult

logger = logging.getLogger(__name__)

MQSS_PENNYLANE_PROFILING_ENABLED = False

@AdapterRegistry.register_adapter
class PennyLaneAdapter(DeviceAdapter):
    name = "mqss_pennylane"

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
        self._token = str(credentials.get("mqss_token") if isinstance(credentials, dict) else None).strip()
        if self._token is None or self._token == "":
            self._token = (MQSS_TOKEN).strip()
        if not self._token:
            raise ValueError(
                "Missing required config: credentials.mqss_token or MQSS_TOKEN"
            )
        
        self._shots = int(adapter_params["shots"]) if adapter_params.get("shots") is not None else None
        # Device will be created lazily in _get_device() when needed

    def _get_device(self, num_qubits):
        """Lazy creation of device (backend) with the specified number of qubits."""
        if not hasattr(self, '_device') or self._device_num_qubits != num_qubits:
            self._device = MQSSPennylaneDevice(
                wires=int(num_qubits),
                token=self._token,
                shots=self._shots,
                backends=self._backend_name,
            )
            self._device_num_qubits = num_qubits
        return self._device

    @override
    def get_backend_name(self) -> str:
        """Return the backend name."""
        return self._backend_name

    @override
    @classmethod
    def validate_profiling_config(cls, profiling_config: ProfilingConfig):
        """Validate profiling parameters."""
        if  profiling_config is None:
            return
        if profiling_config.enabled and not MQSS_PENNYLANE_PROFILING_ENABLED:
            raise ValueError(f"Profiling is no available in {cls.name}.")
        if not profiling_config.metrics: # null or empty means all metrics are requested
            return
        invalid_metrics = set(profiling_config.metrics) - MQSS_VALID_PROFILING_METRICS
        if invalid_metrics:
            raise ValueError(
                f"Invalid profiling metrics for {cls.name}: {invalid_metrics}. "
                f"Valid metrics are: {MQSS_VALID_PROFILING_METRICS}"
            )

    @override
    def execute_circuit(self, context: RunContext, circuit, num_qubits=None, transpile_mode=True) -> ExecutionResult:
        """Given a PennyLane circuit, run it using the PennylaneAdapter

        Args:
            context (RunContext): Context for the benchmark run.
            circuit (qml.qnode): Pennylane Circuit
            num_qubits: number of qubits for device creation.

        Returns:
            ExecutionResult: Result from executing the circuit.
        """
        if num_qubits is None:
            raise ValueError("num_qubits must be provided to create PennyLane device")
        
        if not callable(circuit):
            raise ValueError("circuit must be a callable function")

        device = self._get_device(num_qubits)

        # TODO: for now implement transpile_mode, later consider exploring alternatives to transpilation here
        
        print(f"Running circuit on backend {self._backend_name} ...")
        logger.info("circuit\n%s", circuit)

        result = None

        try:
            result_obj = circuit(device)
        except TypeError:
            result_obj = circuit()

        if callable(result_obj):
            result = result_obj()
        else:
            result = result_obj

        job_result_count = {}
        if isinstance(result, dict):
            job_result_count = result

        # TODO: implement storing job id in pennylane
        if MQSS_PENNYLANE_PROFILING_ENABLED:
            # To be implemented: get profiling data from job_profiler_metrics
            profiling_data = {}  # Placeholder for actual profiling data retrieval
            ...
        else:
            profiling_data = None
        return ExecutionResult(
            job_id=None,
            counts=job_result_count,
            profiling_metrics=ProfilingMetrics(params=profiling_data),
        )