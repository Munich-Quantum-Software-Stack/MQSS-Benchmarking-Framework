"""Analyzers that process raw execution results into insights and visualizations.

Analyzers aggregate measurement counts, compute probabilities, and optionally
generate plots. The base class is subclassed for benchmark-specific analysis logic.
"""

from abc import ABC, abstractmethod
from typing import List, override
from collections import Counter
import matplotlib.pyplot as plt

from .types import RunContext, ExecutionResult, AnalysisResult
from .utils import make_output_filepath

class BenchmarkAnalyzer(ABC):
    """Base class for execution result analyzers.

    Receives a list of ``ExecutionResult`` objects (circuit measurements and metrics)
    and produces an ``AnalysisResult`` with aggregated metrics and optional artifacts.
    Subclasses implement benchmark-specific analysis logic (e.g., fidelity, overlap).
    """
    
    def __init__(self, context: RunContext):
        self.context = context

    @abstractmethod
    def analyze(self, execution_results: List[ExecutionResult], context: RunContext) -> AnalysisResult:
        """Analyze raw execution results."""
        ...


class DefaultAnalyzer(BenchmarkAnalyzer):
    """Standard result aggregator and visualizer.

    Combines all measurement counts, computes outcome probabilities, identifies
    the most frequent bitstring, and optionally generates a probability bar plot.
    Returns metrics and plot artifacts for the benchmark report.
    """

    @override
    def analyze(self, execution_results: List[ExecutionResult], context: RunContext) -> AnalysisResult:
        """Analyze a list of execution results."""
        if not execution_results:
            raise ValueError("No execution results to analyze.")

        combined = Counter()

        for result in execution_results:
            if not isinstance(result.counts, dict):
                raise TypeError("ExecutionResult.counts must be a dict.")
            combined.update(result.counts)

        total_shots = sum(combined.values())
        probabilities = {k: v / total_shots for k, v in combined.items()} if total_shots else {}
        most_frequent = max(combined, key=combined.get) if combined else None

        artifacts = {}
        if context.report_config.analysis.visualization.enabled:
            plot_filename = self._plot(probabilities, context)
            artifacts["plot"] = plot_filename

        return AnalysisResult(
            metrics={
                "total_shots": total_shots,
                "probabilities": probabilities,
                "most_frequent": most_frequent,
            },
            artifacts=artifacts,
        )

    def _plot(self, probabilities: dict, context: RunContext) -> None:
        """Simple probability bar plot."""
        if not probabilities:
            return

        backend_name = context.adapter.get_backend_name()

        plt.figure()
        title = f"Measurement probabilities on {backend_name}" if backend_name else "Measurement probabilities"
        plt.title(title)
        plt.xlabel("Outcome")
        plt.ylabel("Probability")
        plt.grid(axis="y", linestyle="--", alpha=0.5)

        outcomes = list(probabilities.keys())
        probs = list(probabilities.values())

        plt.bar(outcomes, probs)

        filename = make_output_filepath(context.benchmark_key, context.run_dir, tag="plot")
        plt.savefig(filename)

        return filename
