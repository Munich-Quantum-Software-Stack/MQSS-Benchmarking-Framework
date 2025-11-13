"""Adapter registry for managing adapter registration and lookup."""

from __future__ import annotations

import logging
import threading
from typing import Dict, Optional, Type, List, Any
logger = logging.getLogger(__name__)

from .adapter import DeviceAdapter


class AdapterRegistry:
    """Registry for managing adapter classes."""

    _instance: Optional[AdapterRegistry] = None
    _lock = threading.RLock()
    _registry: Dict[str, Type[DeviceAdapter]] = {}

    def __new__(cls) -> AdapterRegistry:
        if cls._instance is None:
            with cls._lock:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Subclassing AdapterRegistry is not allowed.")

    @staticmethod
    def _validate_adapter_name(adapter_name: str) -> None:
        """Validate the adapter name."""
        if not adapter_name or not isinstance(adapter_name, str):
            raise ValueError(f"Invalid adapter name: {adapter_name}")

    def _register(self, adapter_cls: Type[DeviceAdapter]) -> Type[DeviceAdapter]:
        """Register given adapter class."""
        adapter_name = adapter_cls.name
        self._validate_adapter_name(adapter_name)
        if not issubclass(adapter_cls, DeviceAdapter):
            raise TypeError("Only DeviceAdapter subclasses can be registered.")

        with self._lock:
            if adapter_name in self._registry:
                raise ValueError(f"Adapter for adapter name '{adapter_name}' already registered.")
            # copy-on-write for thread-safe reads
            new_registry = dict(self._registry)
            new_registry[adapter_name] = adapter_cls
            self._registry = new_registry

        return adapter_cls

    def _get(self, adapter_name: str, config: Dict[str, Any]) -> DeviceAdapter:
        """Instantiate and return an adapter by adapter name."""
        self._validate_adapter_name(adapter_name)
        try:
            adapter_cls = self._registry[adapter_name]
            return adapter_cls(config)  # instantiate with config
        except KeyError:
            available = ", ".join(sorted(self._registry.keys())) or "none"
            raise ValueError(f"No adapter registered for adapter name '{adapter_name}'. available: {available}")

    def _list_all(self) -> List[str]:
        """List all registered adapter names."""
        return sorted(self._registry.keys())

    @classmethod
    def _clear(cls) -> None:
        """Clear singleton and registry. (usful for test isolation)"""
        with cls._lock:
            cls._registry = {}
            cls._instance = None
            
    # Public API

    @classmethod
    def register_adapter(cls, adapter_cls: Type[DeviceAdapter]) -> Type[DeviceAdapter]:
        """Register given adapter class."""
        return cls()._register(adapter_cls)

    @classmethod
    def get_adapter(cls, adapter_name: str, config: Dict[str, Any]) -> DeviceAdapter:
        """Get an adapter instance by adapter name."""
        return cls()._get(adapter_name, config)

    @classmethod
    def list_adapters(cls) -> List[str]:
        """List all registered adapter names."""
        return cls()._list_all()

