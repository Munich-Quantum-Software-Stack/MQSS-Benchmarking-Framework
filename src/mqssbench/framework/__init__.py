"""Framework module containing base classes and core abstractions."""

from .types import (
    BenchmarkCategory,
    CircuitSpec,
    RunContext,
    CircuitExecutionResult,
    AnalysisResult,
    PipelineResult,
    ReportConfig,
    ProfilingMetrics
)
from .circuit_generator import CircuitGenerator
from .benchmark_executor import (
    BenchmarkExecutor,
    DefaultBenchmarkExecutor,
    HybridBenchmarkExecutor,
)
from .benchmark_analyzer import BenchmarkAnalyzer, DefaultAnalyzer
from .benchmark_pipeline import BenchmarkPipeline
from .benchmark import Benchmark
from .benchmark_registry import BenchmarkRegistry
from .provider import CircuitProvider
from .provider_registry import ProviderRegistry
from .adapter_registry import AdapterRegistry
from .adapter import DeviceAdapter

__all__ = [
    "BenchmarkCategory",
    "CircuitSpec",
    "RunContext",
    "CircuitExecutionResult",
    "AnalysisResult",
    "ReportConfig",
    "ProfilingMetrics",
    "CircuitGenerator",
    "BenchmarkExecutor",
    "DefaultBenchmarkExecutor",
    "HybridBenchmarkExecutor",
    "BenchmarkAnalyzer",
    "DefaultAnalyzer",
    "PipelineResult",
    "BenchmarkPipeline",
    "Benchmark",
    "BenchmarkRegistry",
    "CircuitProvider",
    "ProviderRegistry",
    "AdapterRegistry",
    "DeviceAdapter",
]
