"""Benchmark registry for managing benchmark registration and lookup."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Type

from .utils import validate_benchmark_registry_key

from .benchmark import Benchmark
from .types import RunContext, VALID_ORIGINS


class BenchmarkRegistry:
    """Registry for managing benchmark classes."""

    _instance: Optional[BenchmarkRegistry] = None
    _lock = threading.RLock() # for thread safety
    _registry: Dict[str, Type[Benchmark]] = {}

    def __new__(cls) -> BenchmarkRegistry:
        if cls._instance is None:
            with cls._lock:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Subclassing BenchmarkRegistry is not allowed.")

    @staticmethod
    def _validate_key(identifier: str) -> None:
        """Validate that the identifier follows the origin/source/name format."""
        validate_benchmark_registry_key(identifier)

    def _register(self, benchmark_cls: Type[Benchmark]) -> Type[Benchmark]:
        """Register a benchmark class in the registry."""
        if not issubclass(benchmark_cls, Benchmark):
            raise TypeError("Only Benchmark subclasses can be registered.")
        key = benchmark_cls.registry_key()
        self._validate_key(key)

        with self._lock:
            if key in self._registry:
                raise ValueError(f"Benchmark '{key}' already registered.")
            # copy-on-write for safe lookups during writes
            new_map = dict(self._registry)
            new_map[key] = benchmark_cls
            self._registry = new_map

        return benchmark_cls

    def _get(self, identifier: str) -> Type[Benchmark]:
        """Get a registered benchmark class by its identifier."""
        self._validate_key(identifier)
        try:
            return self._registry[identifier]
        except KeyError:
            raise ValueError(
                f"Benchmark '{identifier}' is not registered."
            )

    def _instantiate(self, identifier: str, context: RunContext) -> Benchmark:
        """Instantiate a benchmark by its identifier with the given context."""
        benchmark_cls = self._get(identifier)
        return benchmark_cls(context)

    def _list_all(self) -> List[str]:
        """List all registered benchmark identifiers."""
        return sorted(self._registry.keys())

    def _list_by_origin(self, origin: str) -> List[str]:
        """List all registered benchmarks for a given origin."""
        if origin not in VALID_ORIGINS:
            raise ValueError(f"Origin '{origin}' must be one of {sorted(VALID_ORIGINS)}.")
        prefix = f"{origin}/"
        return sorted(key for key in self._registry if key.startswith(prefix))

    @classmethod
    def _clear(cls) -> None:
        """Clear singleton and registry. (usful for test isolation)"""
        with cls._lock:
            cls._registry = {}
            cls._instance = None

    # Public API

    @classmethod
    def register_benchmark(cls, benchmark_cls: Type[Benchmark]) -> Type[Benchmark]:
        """
        Decorator to register a Benchmark subclass with the BenchmarkRegistry.

        Example usage:
            @BenchmarkRegistry.register_benchmark
            class MyBenchmark(Benchmark):
                origin = "user"
                source = "my_lib"
                name = "my_benchmark"
        """
        return cls()._register(benchmark_cls)

    @classmethod
    def get_benchmark_class(cls, identifier: str) -> Type[Benchmark]:
        """Get a registered benchmark class by identifier (added class method for convenience)."""
        return cls()._get(identifier)

    @classmethod
    def get_benchmark_instance(cls, identifier: str, context: RunContext) -> Benchmark:
        """Instantiate a benchmark by identifier (added class method for convenience)."""
        return cls()._instantiate(identifier, context)

    @classmethod
    def list_benchmarks(cls, origin: Optional[str] = None) -> List[str]:
        """List registered benchmarks, optionally filtered by origin (added class method for convenience)."""
        instance = cls()
        if origin is None:
            return instance._list_all()
        return instance._list_by_origin(origin)

