"""Profiler for breaking down a benchmark run's HPCQC job cycle.

Reads whatever profiling metrics are actually present on a run (queue time,
compile/transpile time, quantum execution, classical execution, or any of the
MQSS backend's own stage names) and reports/plots only those - metrics that
weren't collected for a given run are simply omitted, never fabricated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import seaborn as sns

from ..framework.types import ExecutionResult, PipelineResult, RunContext
from ..framework.utils import make_output_filepath, show_artifacts

# Known stages in HPCQC job-cycle order; anything else present in the metrics
# (e.g. the MQSS backend's internal stage names) is appended afterward,
# alphabetically, rather than dropped.
_PREFERRED_STAGE_ORDER = (
    "queue_time",
    "transpiler",
    "quantum_software_communication",
    "quantum_execution",
    "classical_execution",
)

_STAGE_LABELS = {
    "queue_time": "Queue",
    "transpiler": "Compile",
    "quantum_software_communication": "Quantum Software + Communication",
    "quantum_execution": "Quantum Execution",
    "classical_execution": "Classical Execution",
}

# Coarse classification for the classical-vs-quantum pie chart: only time the
# QPU itself is actually busy counts as "quantum" - queueing, compiling,
# orchestration/network, and classical optimization are all "classical"
# overhead even though some of them are about the quantum job.
_QUANTUM_STAGE_NAMES = {"quantum_execution"}


def _label_for(name: str) -> str:
    return _STAGE_LABELS.get(name, name.replace("_", " ").title())


def _ordered_keys(raw: Dict[str, Any]) -> List[str]:
    known = [k for k in _PREFERRED_STAGE_ORDER if k in raw]
    rest = sorted(k for k in raw if k not in _PREFERRED_STAGE_ORDER)
    return known + rest


@dataclass(frozen=True)
class ProfileStage:
    """A single, numeric, plottable stage duration."""

    name: str
    label: str
    duration: float


@dataclass(frozen=True)
class ExecutionProfile:
    """Profiling data for one execution within a benchmark run."""

    job_id: Optional[str]
    stages: List[ProfileStage] = field(default_factory=list)
    raw_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_duration(self) -> float:
        return sum(stage.duration for stage in self.stages)


class Profiler:
    """Builds a job-cycle profile from a live run or a saved results.json."""

    def __init__(
        self,
        benchmark_key: str,
        run_id: Optional[str],
        backend: Optional[str],
        executions: List[ExecutionProfile],
        run_dir: str = ".",
    ):
        self.benchmark_key = benchmark_key
        self.run_id = run_id
        self.backend = backend
        self.executions = executions
        self.run_dir = run_dir

    @classmethod
    def from_pipeline_result(
        cls, result: PipelineResult, context: Optional[RunContext] = None
    ) -> "Profiler":
        """Build a profiler from a benchmark run that just executed in-process."""
        executions = [
            cls._build_execution_profile(er.job_id, dict(er.profiling_metrics.params) if er.profiling_metrics else {})
            for er in result.execution_results
        ]
        backend = context.adapter.get_backend_name() if context else None
        run_dir = context.run_dir if context else "."
        return cls(result.benchmark_key, result.run_id, backend, executions, run_dir)

    @classmethod
    def from_manual_metrics(
        cls,
        benchmark_key: str,
        metrics: Dict[str, float],
        run_id: Optional[str] = None,
        backend: Optional[str] = None,
        run_dir: str = ".",
    ) -> "Profiler":
        """Build a profiler from hand-reported values.

        For backends/environments where automatic profiling isn't wired up
        yet (e.g. real hardware timings read off an external dashboard),
        this gives the same report()/plot()/plot_pie() output as a live run
        or a saved results.json.
        """
        execution = cls._build_execution_profile(None, dict(metrics))
        return cls(benchmark_key, run_id, backend, [execution], run_dir)

    @classmethod
    def from_file(cls, path: str) -> "Profiler":
        """Build a profiler from a previously saved results.json."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        executions = [
            cls._build_execution_profile(er.get("job_id"), er.get("profiling_metrics") or {})
            for er in data.get("execution_results", [])
        ]
        backend = (data.get("adapter") or {}).get("backend")
        run_dir = str(Path(path).resolve().parent)
        return cls(
            data.get("benchmark_key", "unknown"),
            data.get("run_id"),
            backend,
            executions,
            run_dir,
        )

    @staticmethod
    def _build_execution_profile(job_id: Optional[str], raw: Dict[str, Any]) -> ExecutionProfile:
        stages = [
            ProfileStage(name=name, label=_label_for(name), duration=float(raw[name]))
            for name in _ordered_keys(raw)
            if isinstance(raw[name], (int, float)) and not isinstance(raw[name], bool)
        ]
        return ExecutionProfile(job_id=job_id, stages=stages, raw_metrics=raw)

    def _get_execution(self, execution_index: int) -> ExecutionProfile:
        if not self.executions:
            raise ValueError("No execution results available to profile.")
        if not (0 <= execution_index < len(self.executions)):
            raise IndexError(
                f"execution_index {execution_index} out of range (0..{len(self.executions) - 1})."
            )
        return self.executions[execution_index]

    def report(self, execution_index: int = 0) -> str:
        """Return a human-readable job-cycle breakdown for one execution."""
        execution = self._get_execution(execution_index)

        lines = [f"Profile: {self.benchmark_key} (run {self.run_id or 'n/a'})"]
        if self.backend:
            lines.append(f"Backend: {self.backend}")

        if not execution.raw_metrics:
            lines.append("No profiling metrics recorded for this run.")
            return "\n".join(lines)

        lines.append("")
        lines.append("Job cycle breakdown:")
        plotted_names = {stage.name for stage in execution.stages}
        for stage in execution.stages:
            lines.append(f"  {stage.label:<24} {stage.duration:>10.3f}s")
        for name in _ordered_keys(execution.raw_metrics):
            if name not in plotted_names:
                lines.append(f"  {_label_for(name):<24} {execution.raw_metrics[name]!r}")

        if execution.stages:
            lines.append(f"  {'Total':<24} {execution.total_duration:>10.3f}s")

        return "\n".join(lines)

    def plot(
        self,
        execution_index: int = 0,
        output_path: Optional[str] = None,
        show: bool = False,
    ) -> Optional[str]:
        """Render the job cycle as a stacked timeline bar and save it to disk.

        Returns the saved plot path, or None if there are no numeric metrics
        to plot for this execution.
        """
        execution = self._get_execution(execution_index)
        if not execution.stages:
            return None

        colors = sns.color_palette("viridis", n_colors=len(execution.stages))

        # Scoped to this plot only - avoids leaking seaborn's global theme
        # into other, unrelated plots (e.g. analyzer plots) drawn later in
        # the same process.
        with sns.axes_style("whitegrid"):
            plt.figure(figsize=(8, 1.8))
            left = 0.0
            for stage, color in zip(execution.stages, colors):
                plt.barh(
                    0, stage.duration, left=left, height=0.35, color=color,
                    label=f"{stage.label} ({stage.duration:.2f}s)",
                )
                left += stage.duration

            plt.ylim(-1, 1)
            plt.yticks([])
            plt.xlabel("Duration (s)")
            title = f"HPCQC job cycle — {self.benchmark_key}"
            if self.backend:
                title += f" on {self.backend}"
            plt.title(title)
            plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.45), ncol=2, fontsize=8, frameon=False)
            sns.despine(left=True)

            path = output_path or make_output_filepath(self.benchmark_key, self.run_dir, tag="profile")
            plt.savefig(path, bbox_inches="tight")
            plt.close()

        if show:
            show_artifacts([path])

        return path

    def plot_pie(
        self,
        execution_index: int = 0,
        output_path: Optional[str] = None,
        show: bool = False,
    ) -> Optional[str]:
        """Render the coarse classical-vs-quantum time split as a pie chart.

        "Quantum" is time the QPU itself is busy (the quantum_execution
        stage); every other recorded stage - queue, compile, orchestration/
        communication, classical optimization, ... - counts as "Classical".
        Returns the saved plot path, or None if there's nothing to plot.
        """
        execution = self._get_execution(execution_index)
        if not execution.stages:
            return None

        quantum_time = sum(s.duration for s in execution.stages if s.name in _QUANTUM_STAGE_NAMES)
        classical_time = execution.total_duration - quantum_time

        slices = [
            (label, value)
            for label, value in (("Classical", classical_time), ("Quantum", quantum_time))
            if value > 0
        ]
        if not slices:
            return None

        colors = sns.color_palette("viridis", n_colors=len(slices))

        with sns.axes_style("white"):
            plt.figure(figsize=(5, 5))
            labels = [f"{label} ({value:.1f}s)" for label, value in slices]
            plt.pie(
                [value for _, value in slices],
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops={"linewidth": 1, "edgecolor": "white"},
            )
            title = f"Classical vs quantum time — {self.benchmark_key}"
            if self.backend:
                title += f" on {self.backend}"
            plt.title(title)

            path = output_path or make_output_filepath(self.benchmark_key, self.run_dir, tag="profile_pie")
            plt.savefig(path, bbox_inches="tight")
            plt.close()

        if show:
            show_artifacts([path])

        return path
