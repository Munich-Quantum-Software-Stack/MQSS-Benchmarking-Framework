"""Root pipeline abstraction for benchmark execution."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .types import PipelineResult, RunContext


class BenchmarkPipeline(ABC):
    """Abstract base class for all benchmark pipelines.
    
    Subclasses must define the following class-level attributes:
    - ``origin``, ``source``, ``name``: used to build the benchmark registry key
        with ``registry_key()`` (format: "origin/source/name").
    - ``get_category``: a method that returns a category label for the benchmark.
    - ``run``: a method that executes the benchmark pipeline and returns a ``PipelineResult``.

    helpful methods:
    - ``registry_key()``: returns the stable registry key string.
    """

    origin: str
    source: str
    name: str

    def __init__(self, context: RunContext):
        self.context = context

    @classmethod
    def registry_key(cls) -> str:
        """Registry key in origin/source/name format."""
        return f"{cls.origin}/{cls.source}/{cls.name}"

    @abstractmethod
    def run(self) -> PipelineResult:
        """Run the pipeline and return a structured result."""
        ...

    @abstractmethod
    def get_category(self) -> str:
        """Return a category label for this pipeline."""
        ...
