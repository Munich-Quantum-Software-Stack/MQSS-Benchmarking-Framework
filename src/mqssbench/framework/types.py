"""Core data structures and types for the benchmarking framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Any, Dict, Optional, Literal, TYPE_CHECKING
from pathlib import Path

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
class VisualizationConfig:
    enabled: bool = False  # generate visualization artifacts
    show: bool = False  # display interactively

    def __post_init__(self):
        if self.show and not self.enabled:
            raise ValueError("show=True requires visualization.enabled=True")


@dataclass(frozen=True)
class AnalysisConfig:
    enabled: bool = True
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)


@dataclass(frozen=True)
class ReportConfig:
    """Configuration for generated reports."""

    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)

    def __post_init__(self):
        # Validate that visualization only applies if analysis is enabled
        if self.analysis.visualization.enabled and not self.analysis.enabled:
            raise ValueError("Visualization can only be True if analysis is enabled.")


@dataclass(frozen=True)
class FileStorageConfig:
    format: Literal["json"] = "json"


@dataclass(frozen=True)
class SqliteStorageConfig:
    db_path: str

    def __post_init__(self):
        # Ensure the path is not empty
        if not self.db_path:
            raise ValueError("db_path must be provided for sqlite storage")
        # Enforce relative path (relative to output_dir) for safety
        db_path_obj = Path(self.db_path)
        if db_path_obj.is_absolute():
            raise ValueError("db_path must be relative to output_dir for safety")


@dataclass(frozen=True)
class StorageConfig:
    """Configuration for persisting benchmark results."""

    enabled: bool = False
    type: Literal["file", "sqlite"] = "file"
    file: Optional[FileStorageConfig] = field(default_factory=FileStorageConfig)
    sqlite: Optional[SqliteStorageConfig] = (
        None  # field(default_factory=SqliteStorageConfig)
    )

    def __post_init__(self):
        # Validate type and corresponding config
        if self.type == "file" and self.file is None:
            raise ValueError("file config must be provided when type='file'")
        if self.type == "sqlite" and self.sqlite is None:
            raise ValueError("sqlite config must be provided when type='sqlite'")


@dataclass(frozen=True)
class RunContext:
    """Context for a benchmark run."""

    run_id: str
    run_dir: str  # to store per-run data/artifacts
    adapter: "DeviceAdapter"  # Forward reference to avoid circular import
    benchmark_key: str
    params: Dict[str, Any] = field(default_factory=dict)  # benchmark parameters
    report_config: ReportConfig = field(default_factory=ReportConfig)
    profiling: Optional[ProfilingConfig] = field(default_factory=ProfilingConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProfilingMetrics:
    """Profiling output keyed by param name (e.g., 'transpiler')."""

    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    """Result from executing a circuit."""

    job_id: str
    counts: Any
    profiling_metrics: ProfilingMetrics = field(default_factory=ProfilingMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)
    exp_value: Optional[float] = None  # expected value, if applicable
    optimal_params: Optional[list[float]] = None  # optimal params, if applicable


@dataclass(frozen=True)
class AnalysisResult:
    """Analysis results from executing a circuit."""

    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)  # name -> filepath


@dataclass(frozen=True)
class BenchmarkResult:
    """Final result from a benchmark run."""

    run_id: str
    benchmark_key: str
    params: Dict[str, Any] = field(default_factory=dict)  # benchmark parameters
    execution_results: list[ExecutionResult] = field(default_factory=list)
    analysis_result: Optional[AnalysisResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    storage_location: Optional[str] = None
