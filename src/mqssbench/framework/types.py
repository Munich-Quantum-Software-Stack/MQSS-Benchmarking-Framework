"""Core data structures and types for the benchmarking framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Any, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from mqssbench.framework.adapter import DeviceAdapter

# Valid origins for benchmarks
VALID_ORIGINS = frozenset({"core", "user"})

class BenchmarkCategory(StrEnum):
    """Category classification for benchmarks."""
    HARDWARE = auto()
    SOFTWARE = auto()
    ALGORITHM = auto()
    SIMULATOR = auto()


CircuitType = Any


@dataclass(frozen=True)
class CircuitSpec:
    """Specification for a circuit to be executed."""
    circuit: CircuitType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProfilingConfig:
    """Configuration for profiling during circuit execution."""
    enabled: bool = False
    metrics: Optional[list[str]] = None  # List of metrics to collect, or None for all


@dataclass(frozen=True)
class OutputConfig:
    """Configuration for saving and handling output results."""

    analysis: bool = True
    visualization: bool = False  # only meaningful if analysis is True
    save: bool = False
    output_dir: str = ""  # required if save is True

    def __post_init__(self):
        # Validate that visualization only applies if analysis is enabled
        if self.visualization and not self.analysis:
            raise ValueError("Visualization can only be True if analysis is enabled.")

        # Validate that output_dir is provided if save is True
        if self.save and not self.output_dir:
            raise ValueError("output_dir must be provided when save is True.")


@dataclass(frozen=True)
class RunContext:
    """Context for a benchmark run."""
    adapter: "DeviceAdapter"  # Forward reference to avoid circular import
    benchmark_key: str
    params: Dict[str, Any] = field(default_factory=dict)
    output_config: OutputConfig = field(default_factory=OutputConfig)
    profiling: Optional[ProfilingConfig] = field(default_factory=ProfilingConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProfilingMetrics:
    """Profiling output keyed by param name (e.g., 'transpiler')."""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    """Result from executing a circuit."""
    counts: Any
    profiling_metrics: ProfilingMetrics = field(default_factory=ProfilingMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisResult:
    """Analysis results from executing a circuit."""
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchmarkResult:
    """Final result from a benchmark run."""
    benchmark_key: str
    params: Dict[str, Any] = field(default_factory=dict)
    execution_results: list[ExecutionResult] = field(default_factory=list)
    analysis_result: Optional[AnalysisResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
