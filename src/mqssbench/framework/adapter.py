"""MQSS adapter base class."""

from abc import ABC, abstractmethod
from .types import ProfilingConfig, RunContext, ExecutionResult


class DeviceAdapter(ABC):
    """Abstract base class for MQSS adapters."""

    name: str  # Unique name for the adapter class. Child classes must define this attribute

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Validate class attributes
        if "name" not in cls.__dict__ or not isinstance(
            getattr(cls, "name", None), str
        ):
            raise TypeError(
                f"{cls.__name__}: missing or invalid 'name' class attribute."
            )

    def __init__(self, config):
        """Initialize the adapter with the given configuration."""
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """Return the backend name."""
        ...

    @classmethod
    @abstractmethod
    def validate_profiling_config(cls, profiling_config: ProfilingConfig):
        """Validate profiling parameters."""
        ...

    @abstractmethod
    def execute_circuit(
        self, context: RunContext, circuit, num_qubits=None, transpile_mode=True
    ) -> ExecutionResult:
        """Execute a circuit on the backend."""
        ...

        # TODO: add batch circuits running for efficiency
