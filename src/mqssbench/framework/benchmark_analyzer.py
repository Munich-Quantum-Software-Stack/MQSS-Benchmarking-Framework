"""Benchmark analyzer abstraction."""

from abc import ABC, abstractmethod
from typing import List, override
from collections import Counter
import matplotlib.pyplot as plt

from .types import RunContext, ExecutionResult, AnalysisResult
from .utils import make_output_path, safe_plot_show

class BenchmarkAnalyzer(ABC):
    """Abstract base class for benchmark analyzers."""
    
    def __init__(self, context: RunContext):
        self.context = context

    @abstractmethod
    def analyze(self, execution_results: List[ExecutionResult], context: RunContext) -> AnalysisResult:
        """Analyze raw execution results."""
        ...


class DefaultAnalyzer(BenchmarkAnalyzer):
    """ Default benchmark analyzer for aggregating execution results."""

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

        if context.output_config.visualization:
            self._plot(probabilities, context)

        return AnalysisResult({
            "total_shots": total_shots,
            "probabilities": probabilities,
            "most_frequent": most_frequent,
        })

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

        if context.output_config.save:
            bench_name = context.benchmark_key.split("/")[-1]
            filename = make_output_path(name=bench_name, output_dir=context.output_config.output_dir, is_plot=True)
            plt.savefig(filename)

        # safe plot show to avoid calling plt.show() which blocks in In CI / headless environments
        safe_plot_show()
