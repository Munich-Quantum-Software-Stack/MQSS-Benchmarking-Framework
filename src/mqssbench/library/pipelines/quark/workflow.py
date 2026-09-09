"""QUARK benchmark pipeline integration."""

from __future__ import annotations

import importlib.util
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from statistics import fmean
from textwrap import wrap
from typing import Any

import yaml

from mqssbench.framework.benchmark_pipeline import BenchmarkPipeline
from mqssbench.framework.types import (
    AnalysisResult,
    BenchmarkCategory,
    BenchmarkRunStatus,
    PipelineEngineExecutionResult,
    PipelineResult,
    RunContext,
)

logger = logging.getLogger(__name__)

try:
    from quark.benchmarking import (
        FailedPipelineRun,
        FinishedPipelineRun,
        FinishedTreeRun,
        InterruptedTreeRun,
        ModuleRunMetrics,
        run_pipeline_tree,
    )
    from quark.config_parsing import Config, parse_config
    from quark.interface_types import Other
    from quark.plugin_manager.loader import load_plugins

    _QUARK_AVAILABLE = True
except ImportError:
    _QUARK_AVAILABLE = False


def _parse_quark_config(quark_config: str | dict[str, Any]) -> Config:
    """Pass an opaque QUARK config through QUARK's parser."""
    if isinstance(quark_config, str):
        return parse_config(quark_config)

    if isinstance(quark_config, dict):
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False,
            encoding="utf-8",
        ) as handle:
            yaml.safe_dump(quark_config, handle)
            temp_path = Path(handle.name)

        try:
            return parse_config(str(temp_path))
        finally:
            temp_path.unlink()

    raise TypeError("quark_config must be a file path or a dict")


def _extract_numeric_result(result: Any) -> float | None:
    """Extract a numeric result for aggregate statistics."""
    if isinstance(result, Other):
        result = result.data

    if isinstance(result, bool):
        return None

    if isinstance(result, int | float):
        return float(result)

    return None


def _serialize_result(result: Any) -> float:
    """Serialize a QUARK pipeline result as a numeric JSON value."""
    numeric = _extract_numeric_result(result)

    if numeric is None:
        raise TypeError(
            f"Expected numeric pipeline result, got {type(result).__name__}"
        )

    return numeric


def _pipeline_runtime(steps: list[ModuleRunMetrics]) -> float:
    """Return QUARK's pipeline runtime represented by module timings.

    QUARK's FinishedPipelineRun does not store a separate runtime field.
    Its documented metrics contain preprocess/postprocess times for each
    executed module, so the pipeline total is their sum.
    """
    return sum(step.preprocess_time + step.postprocess_time for step in steps)


def _mean(values: list[float]) -> float | None:
    """Return the arithmetic mean, or None for an empty input."""
    if not values:
        return None

    return float(fmean(values))


def _step_record(step: ModuleRunMetrics) -> dict[str, Any]:
    """Serialize one QUARK ModuleRunMetrics record."""
    return {
        "module_info": {
            "name": step.module_info.name,
            "params": dict(step.module_info.params),
        },
        "preprocess_time": step.preprocess_time,
        "postprocess_time": step.postprocess_time,
        "additional_metrics": dict(step.additional_metrics),
        "unique_name": step.unique_name,
    }


def _pipeline_name(
    pipeline_run: FinishedPipelineRun | FailedPipelineRun,
) -> str:
    """Build pipeline name from QUARK step names."""
    pipeline_name: str = ""

    if isinstance(pipeline_run, FinishedPipelineRun):
        pipeline_name = "-".join(
            step.unique_name
            for step in pipeline_run.steps
        )
    elif isinstance(pipeline_run, FailedPipelineRun):
        # TODO: to match the pipeline name exactly like QUARK, later we should add a index to the beginning of the pipeline name
        pipeline_name = "-".join(
            step.unique_name
            for step in pipeline_run.metrics_up_to_now
        )

    return pipeline_name


def _finished_run_record(
    pipeline_run: FinishedPipelineRun,
) -> dict[str, Any]:
    """Serialize one QUARK FinishedPipelineRun."""
    steps = [_step_record(step) for step in pipeline_run.steps]

    return {
        "pipeline": _pipeline_name(pipeline_run),
        "result": _serialize_result(pipeline_run.result),
        "runtime": _pipeline_runtime(pipeline_run.steps),
        "steps": steps,
    }


def _failed_run_record(
    failed_run: FailedPipelineRun,
) -> dict[str, Any]:
    """Serialize one QUARK FailedPipelineRun."""
    return {
        "pipeline": _pipeline_name(failed_run),
        "reason": failed_run.reason,
        "steps": [
            _step_record(step)
            for step in failed_run.metrics_up_to_now
        ],
    }


def _additional_metrics(
    finished_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    additional_metrics: list[dict[str, Any]] = []

    for record in finished_records:
        pipeline_metrics = {
            step["unique_name"]: step["additional_metrics"]
            for step in record["steps"]
            if step["additional_metrics"]
        }

        if pipeline_metrics:
            additional_metrics.append(pipeline_metrics)

    return additional_metrics


def _execution_result_from_quark_record(
    record: dict[str, Any],
    *,
    pipeline_status: str,
    index: int,
) -> PipelineEngineExecutionResult:
    """Store raw QUARK pipeline records directly in the execution payload."""
    payload = dict(record)
    pipeline_name = payload.pop("pipeline", f"{pipeline_status}-{index}")

    return PipelineEngineExecutionResult(
        pipeline=str(pipeline_name),
        pipeline_status=pipeline_status,
        payload=payload,
    )


def _plot_results(
    finished_records: list[dict[str, Any]],
    context: RunContext,
) -> str | None:
    """Write QUARK's horizontal results bar chart as results.pdf."""
    bar_items = [
        (
            "\n".join(wrap(record["pipeline"], 25)),
            record["result"],
        )
        for record in finished_records
        if isinstance(record["result"], (int, float))
    ]

    if not bar_items:
        return None

    import matplotlib.pyplot as plt

    bar_items.sort(key=lambda item: item[1], reverse=True)

    plt.figure()
    plt.barh(
        [item[0] for item in bar_items],
        [item[1] for item in bar_items],
    )
    plt.title("Results")
    plt.ylabel("Pipelines")
    plt.yticks(fontsize=5)
    plt.xlabel("Result")
    plt.tight_layout()

    artifact_dir = Path(context.run_dir) / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    filename = artifact_dir / "results.pdf"
    plt.savefig(filename)
    plt.close()

    return str(filename)


def analyze_quark_output(
    tree_results: list[FinishedTreeRun | InterruptedTreeRun],
    context: RunContext,
) -> AnalysisResult | None:
    """Build the MBF analysis result from QUARK tree runs."""
    if not context.report_config.analysis.enabled:
        return None

    finished_pipeline_runs: list[FinishedPipelineRun] = []
    failed_pipeline_runs: list[FailedPipelineRun] = []

    successful_tree_runs_count = 0

    for tree_result in tree_results:
        finished_pipeline_runs.extend(tree_result.finished_pipeline_runs)

        if isinstance(tree_result, FinishedTreeRun):
            successful_tree_runs_count += 1
        elif isinstance(tree_result, InterruptedTreeRun):
            failed_pipeline_runs.extend(tree_result.failed_pipeline_runs)

    finished_pipeline_records = [
        _finished_run_record(run)
        for run in finished_pipeline_runs
    ]

    numeric_results = [
        record["result"]
        for record in finished_pipeline_records
        if isinstance(record["result"], (int, float))
    ]

    runtimes = [
        record["runtime"]
        for record in finished_pipeline_records
    ]

    successful_pipeline_runs_count = len(finished_pipeline_runs)
    failed_pipeline_runs_count = len(failed_pipeline_runs)
    total_pipeline_runs = successful_pipeline_runs_count + failed_pipeline_runs_count

    total_tree_runs = len(tree_results)

    metrics: dict[str, Any] = {
        "successful_tree_runs": (
            f"{successful_tree_runs_count}/{total_tree_runs}"
        ),
        "successful_pipeline_runs": (
            f"{successful_pipeline_runs_count}/{total_pipeline_runs}"
        ),
        "average_runtime": _mean(runtimes),
        "average_result": _mean(numeric_results),
        "additional_metrics": _additional_metrics(finished_pipeline_records),
    }

    artifacts: dict[str, str] = {}
    if context.report_config.analysis.visualization.enabled:
        plot_path = _plot_results(finished_pipeline_records, context)
        if plot_path:
            artifacts["results.pdf"] = plot_path

    return AnalysisResult(metrics=metrics, artifacts=artifacts)


def get_pipeline_result(
    context: RunContext,
    tree_results: list[FinishedTreeRun | InterruptedTreeRun],
) -> PipelineResult:
    """Build the MBF pipeline result from QUARK tree runs."""
    status = (
        BenchmarkRunStatus.FAILED
        if any(
            isinstance(result, InterruptedTreeRun)
            for result in tree_results
        )
        else BenchmarkRunStatus.COMPLETED
    )

    finished_pipeline_records = [
        _finished_run_record(run)
        for tree_result in tree_results
        for run in getattr(tree_result, "finished_pipeline_runs", [])
    ]
    failed_pipeline_records = [
        _failed_run_record(run)
        for tree_result in tree_results
        for run in getattr(tree_result, "failed_pipeline_runs", [])
    ]

    execution_results = [
        _execution_result_from_quark_record(
            record,
            pipeline_status="finished",
            index=i,
        )
        for i, record in enumerate(finished_pipeline_records)
    ] + [
        _execution_result_from_quark_record(
            record,
            pipeline_status="failed",
            index=i,
        )
        for i, record in enumerate(failed_pipeline_records)
    ]

    return PipelineResult(
        run_id=context.run_id,
        benchmark_key=context.benchmark_key,
        category=BenchmarkCategory.APPLICATION,
        status=status,
        params=dict(context.params),
        execution_results=execution_results,
        analysis_result=analyze_quark_output(tree_results, context),
    )


def ensure_plugins_installed(plugins: list[str]) -> None:
    """Install missing QUARK plugins using uv."""
    missing = [
        plugin
        for plugin in plugins
        if importlib.util.find_spec(plugin) is None
    ]

    if not missing:
        return

    packages = [
        plugin.replace("_", "-")
        for plugin in missing
    ]

    logger.info(
        "Installing missing QUARK plugins: %s",
        ", ".join(packages),
    )

    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError(
            "uv is required to install missing QUARK plugins."
        )

    subprocess.run(
        ["uv", "pip", "install", *packages],
        check=True,
    )

    logger.info("Successfully installed QUARK plugins.")

    still_missing = [
        plugin
        for plugin in plugins
        if importlib.util.find_spec(plugin) is None
    ]

    if still_missing:
        raise RuntimeError(
            "Unable to install missing QUARK plugins: "
            f"{', '.join(still_missing)}"
        )


if _QUARK_AVAILABLE:

    class QUARKBenchmarkPipeline(BenchmarkPipeline):
        """Run a QUARK pipeline from an opaque QUARK config."""

        origin = "core"
        source = "quark"
        name = "workflow"

        def __init__(self, context: RunContext):
            super().__init__(context)

            quark_config = context.params.get("quark_config")
            if quark_config is None:
                raise ValueError(
                    "QUARK benchmark params must include 'quark_config' (file path)."
                )

            self.parsed_config = _parse_quark_config(quark_config)

        def get_category(self) -> str:
            return BenchmarkCategory.APPLICATION

        def run(self) -> PipelineResult:
            # install_plugins is a parameter that can be set in the benchmark config to control
            # whether QUARK plugins should be installed automatically. By default, it is set to True.
            if self.context.params.get("install_plugins", True):
                ensure_plugins_installed(self.parsed_config.plugins)
            load_plugins(self.parsed_config.plugins)

            # failfast is a QUARK feature that stops the pipeline tree execution on the first failure. by default, it is set to False.
            failfast = bool(self.context.params.get("failfast", False))
            tree_results = [
                run_pipeline_tree(tree, failfast=failfast)
                for tree in self.parsed_config.pipeline_trees
            ]

            return get_pipeline_result(self.context, tree_results)

else:
    QUARKBenchmarkPipeline = None


def register() -> None:
    """Plugin registration hook."""
    if QUARKBenchmarkPipeline is None:
        logger.debug("quark not installed; skipping QUARK pipeline registration")
        return

    from mqssbench.framework.benchmark_registry import BenchmarkRegistry

    BenchmarkRegistry.register_benchmark(QUARKBenchmarkPipeline)