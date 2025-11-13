"""Circuit generator abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .types import CircuitSpec, RunContext


class CircuitGenerator(ABC):
    """Abstract base class for circuit generators."""
    
    def __init__(self, context: RunContext):
        self.context = context

    @abstractmethod
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:
        """Generate circuits based on the provided parameters."""
        ...

