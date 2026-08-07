"""Circuit providers that supply pre-built or parameterized circuits.

Providers expose external circuit libraries (e.g., benchmark suites, standard tests)
with a simple interface: list available circuits and retrieve them by name.
Each provider must define a unique ``name`` identifier.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

# since we auto resister all avaialable circuits from a provider, having a limit is a safer approach
MAX_CIRCUITS_PER_PROVIDER = (
    100  # TODO: this should be controlled by by the framework, not by the implementer
)


class CircuitProvider(ABC):
    """Abstract interface for circuit providers.

    Subclasses must define the ``name`` class attribute (unique string identifier).
    The ``__init_subclass__`` hook validates this at class definition time.

    Key methods:
    - ``list_available()``: returns list of circuit names provided by this source.
    - ``get_circuit()``: returns a circuit object for the given name and parameters.
    """

    name: str  # Unique name for the provider class. Child classes must define this attribute

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Validate class attributes
        if "name" not in cls.__dict__ or not isinstance(
            getattr(cls, "name", None), str
        ):
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
