"""Benchmark base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, Type, TypeVar

from .utils import validate_benchmark_registry_key

from .types import BenchmarkCategory, RunContext, BenchmarkResult
from .circuit_generator import CircuitGenerator
from .benchmark_executor import BenchmarkExecutor, HybridBenchmarkExecutor
from .benchmark_analyzer import BenchmarkAnalyzer

ComponentT = TypeVar(
    "ComponentT", CircuitGenerator, BenchmarkExecutor, BenchmarkAnalyzer
)


class Benchmark(ABC):
    """Base class for all benchmarks.

    Subclasses must define the following class-level attributes:
    - ``origin``, ``source``, ``name``: used to build the benchmark registry key
        with ``registry_key()`` (format: "origin/source/name").
    - ``generator``, ``executor``, ``analyzer``: classes used during ``run()``
        to generate circuits, execute them, and analyze results.
    - ``supported_adapters``: tuple of adapter names (empty tuple = no restriction).
    - ``category``: a ``BenchmarkCategory`` instance describing the benchmark type.

    Implementations must override ``validate_params(self, params)`` to validate
    benchmark-specific parameters.

    Optionally override ``validate_context`` to perform context-specific checks.

    The ``run()`` method performs the common workflow: validate inputs,
    instantiate components, execute the benchmark, optionally run analysis,
    and return a ``BenchmarkResult``.

    Helper methods:
    - ``registry_key()``: returns the stable registry key string.
    - ``_instantiate_component()``: ensures a component is a class and a
        subclass of the expected type, then instantiates it with the current
        ``context``.
    - ``_validate_attributes()``: verifies all required class attributes and
        types at subclass definition time.
    """

    # Class-level attributes that must be defined by subclasses
    origin: str
    source: str
    name: str
    generator: Type[CircuitGenerator]
    executor: Type[BenchmarkExecutor]
    analyzer: Type[BenchmarkAnalyzer]
    supported_adapters: Tuple[str, ...]  # Empty tuple means unrestricted
    category: BenchmarkCategory

    def __init__(self, context: RunContext):
        self.context = context

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._validate_attributes()

    @classmethod
    def registry_key(cls) -> str:
        """Generate the registry key for this benchmark."""
        return f"{cls.origin}/{cls.source}/{cls.name}"

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate benchmark parameters."""
        ...

    def validate_adapter(self, adapter_name: str) -> None:
        """Validate that the adapter is supported."""
        if self.supported_adapters:
            if adapter_name not in self.supported_adapters:
                raise ValueError(
                    f"Benchmark '{self.registry_key()}' supports adapters {self.supported_adapters}; "
                    f"got '{adapter_name}'."
                )

    def validate_context(self, context: RunContext) -> None:
        """Validate the run context."""
        ...

    def run(self) -> BenchmarkResult:
        """Execute the benchmark."""
        self.validate_params(self.context.params)
        self.validate_adapter(self.context.adapter.name)
        self.validate_context(self.context)

        generator = self._instantiate_component(self.generator, CircuitGenerator)
        circuits = generator.generate(self.context.params)

        executor = self._instantiate_component(self.executor, BenchmarkExecutor)

        if isinstance(executor, HybridBenchmarkExecutor):
            excecution_results = executor.run(generator, self.context)
        else:
            excecution_results = executor.run(circuits, self.context)

        analysis_result = None
        if self.context.report_config.analysis.enabled:
            analyzer = self._instantiate_component(self.analyzer, BenchmarkAnalyzer)
            analysis_result = analyzer.analyze(excecution_results, self.context)

        return BenchmarkResult(
            run_id=self.context.run_id,
            benchmark_key=self.context.benchmark_key,
            params=self.context.params,
            execution_results=excecution_results,
            analysis_result=analysis_result,
        )

    def _instantiate_component(
        self,
        component: Type[ComponentT],
        expected_type: Type[ComponentT],
    ) -> ComponentT:
        """Resolve a component class to an instance."""
        if not isinstance(component, type):
            raise TypeError(f"{expected_type.__name__} must be provided as a class.")
        if not issubclass(component, expected_type):
            raise TypeError(
                f"{component.__name__} must be a subclass of {expected_type.__name__}."
            )
        return component(self.context)  # type: ignore[arg-type]

    @classmethod
    def _validate_attributes(cls) -> None:
        """Validate benchmark class attributes."""

        required_attrs = [
            "origin",
            "source",
            "name",
            "generator",
            "executor",
            "analyzer",
            "supported_adapters",
            "category",
        ]
        for attr in required_attrs:
            if attr not in cls.__dict__:
                raise TypeError(
                    f"Benchmark class '{cls.__name__}' must define '{attr}' at the class level."
                )

        validate_benchmark_registry_key(cls.registry_key())

        if not issubclass(cls.generator, CircuitGenerator):
            raise TypeError("generator must be a subclass of CircuitGenerator.")
        if not issubclass(cls.executor, BenchmarkExecutor):
            raise TypeError("executor must be a subclass of BenchmarkExecutor.")
        if not issubclass(cls.analyzer, BenchmarkAnalyzer):
            raise TypeError("analyzer must be a subclass of BenchmarkAnalyzer.")

        if not isinstance(cls.supported_adapters, tuple):
            raise TypeError("supported_adapters must be a tuple of strings.")
        for adapter in cls.supported_adapters:
            if not isinstance(adapter, str):
                raise TypeError("supported_adapters must be a tuple of strings.")

        if not isinstance(cls.category, BenchmarkCategory):
            raise TypeError("category must be an instance of BenchmarkCategory.")
