"""Circuit provider abstraction for external circuit libraries."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

# since we auto resister all avaialable circuits from a provider, having a limit is a safer approach
MAX_CIRCUITS_PER_PROVIDER = 100 # TODO: this should be controlled by by the framework, not by the implementer


class CircuitProvider(ABC):
    """Abstract base class for circuit providers."""

    name: str # Unique name for the provider class. Child classes must define this attribute

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Validate class attributes
        if "name" not in cls.__dict__ or not isinstance(getattr(cls, "name", None), str):
            raise TypeError(
                f"{cls.__name__}: missing or invalid 'name' class attribute."
            )

    @abstractmethod
    def list_available(self) -> List[str]:
        """List available circuit names from this provider."""
        ...

    @abstractmethod
    def get_circuit(self, circuit_name: str, params: Dict[str, Any]) -> Any:
        """Get a circuit by name with the given parameters."""
        ...
