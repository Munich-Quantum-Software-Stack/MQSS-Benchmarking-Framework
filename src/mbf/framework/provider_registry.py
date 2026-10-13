"""Circuit provider registry for managing circuit provider registration and lookup."""

from __future__ import annotations

import logging
import threading
from typing import Dict, Type, List, Optional
from .provider import CircuitProvider

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """Registry for managing circuit provider classes."""

    _instance: Optional[ProviderRegistry] = None
    _lock = threading.RLock()
    _registry: Dict[str, Type[CircuitProvider]] = {}

    def __new__(cls) -> ProviderRegistry:
        if cls._instance is None:
            with cls._lock:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Subclassing ProviderRegistry is not allowed.")

    @staticmethod
    def _validate_source(source: str) -> None:
        """Validate the source name."""
        if not source or not isinstance(source, str):
            raise ValueError(f"Invalid source name: {source}")

    def _register(self, provider_cls: Type[CircuitProvider]) -> Type[CircuitProvider]:
        """Register a provider class (stores class, not instance)."""
        source = provider_cls.name
        self._validate_source(source)

        with self._lock:
            if source in self._registry:
                raise ValueError(f"Circuit provider '{source}' already registered.")
            # copy-on-write for thread-safe reads
            new_registry = dict(self._registry)
            new_registry[source] = provider_cls
            self._registry = new_registry

        return provider_cls

    def _get(self, source: str) -> CircuitProvider:
        """Instantiate and return a provider by source name."""
        self._validate_source(source)
        try:
            provider_cls = self._registry[source]
            return provider_cls()  # lazy instantiate
        except KeyError:
            available = ", ".join(sorted(self._registry.keys())) or "none"
            raise ValueError(f"No circuit provider registered for source '{source}'. available: {available}")

    def _list_all(self) -> List[str]:
        """List all registered source names."""
        return sorted(self._registry.keys())

    @classmethod
    def _clear(cls) -> None:
        """Clear singleton and registry. (usful for test isolation)"""
        with cls._lock:
            cls._registry = {}
            cls._instance = None

    # Public API

    @classmethod
    def register_provider(cls, provider_cls: Type[CircuitProvider]) -> Type[CircuitProvider]:
        """Decorator to register a provider class."""
        return cls()._register(provider_cls)

    @classmethod
    def get_provider(cls, source: str) -> CircuitProvider:
        """Get a provider instance by source name."""
        return cls()._get(source)

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered provider source names."""
        return cls()._list_all()
