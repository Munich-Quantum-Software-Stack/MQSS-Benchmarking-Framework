"""QUARK benchmark pipeline integration."""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Any
import importlib.util
import subprocess
import shutil
import yaml

from mqssbench.framework.benchmark_pipeline import BenchmarkPipeline
from mqssbench.framework.types import PipelineResult, RunContext, AnalysisResult, BenchmarkRunStatus, BenchmarkCategory

logger = logging.getLogger(__name__)

try:
    from quark.benchmarking import (
        FinishedTreeRun,
        InterruptedTreeRun,
        ModuleRunMetrics,
        run_pipeline_tree,
    )
    from quark.config_parsing import Config, parse_config
    from quark.plugin_manager.loader import load_plugins

    _QUARK_AVAILABLE = True
except ImportError:
    _QUARK_AVAILABLE = False


def _parse_quark_config(quark_config: str | dict[str, Any]) -> Config:
    """Pass opaque QUARK config to QUARK's public parser."""
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
            temp_path = handle.name
        try:
            return parse_config(temp_path)
        finally:
            os.unlink(temp_path)

    raise TypeError("quark_config must be a file path or a dict")


def _step_metrics(step: ModuleRunMetrics) -> dict[str, Any]:
    return {
        "module": step.module_info.name,
        "module_params": dict(step.module_info.params),
        "preprocess_time": step.preprocess_time,
        "postprocess_time": step.postprocess_time,
        "additional_metrics": dict(step.additional_metrics),
        "unique_name": step.unique_name,
    }


def _finished_pipeline_metrics(pipeline_run: Any) -> dict[str, Any]:
    return {
        "steps": [_step_metrics(step) for step in pipeline_run.steps],
    }


def _metrics_from_tree_run(
    tree_result: FinishedTreeRun | InterruptedTreeRun,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "finished_pipeline_runs": [
            _finished_pipeline_metrics(run)
            for run in tree_result.finished_pipeline_runs
        ],
    }

    if isinstance(tree_result, InterruptedTreeRun):
        metrics["failed_pipeline_runs"] = [
            {
                "reason": failed.reason,
                "steps": [_step_metrics(step) for step in failed.metrics_up_to_now],
            }
            for failed in tree_result.failed_pipeline_runs
        ]

    return metrics


def _base_pipeline_result(context: RunContext, status: BenchmarkRunStatus, metrics: dict[str, Any]) -> PipelineResult:
    analysis_result = None
    if getattr(context, "report_config", None) and getattr(context.report_config, "analysis", None) and getattr(context.report_config.analysis, "enabled", False):
        # Create the default analysis result from QUARK metrics.
        # TODO: Implement artifact mapping if needed, or perform custom analysis outside the pipeline.        
        analysis_result = AnalysisResult(
            metrics=metrics,
            artifacts={}
        )
    return PipelineResult(
        run_id=context.run_id,
        benchmark_key=context.benchmark_key,
        category=BenchmarkCategory.APPLICATION,
        status=status,
        params=dict(context.params),
        analysis_result=analysis_result,
    )


def _merge_tree_metrics(tree_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    if len(tree_metrics) == 1:
        return tree_metrics[0]

    return {"pipeline_trees": tree_metrics}


def ensure_plugins_installed(plugins: list[str]) -> None:
    """Install missing QUARK plugins using uv."""

    missing = [
        plugin
        for plugin in plugins
        if importlib.util.find_spec(plugin) is None
    ]

    if not missing:
        return

    packages = [plugin.replace("_", "-") for plugin in missing]

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

    # Verify installation
    still_missing = [
        plugin
        for plugin in plugins
        if importlib.util.find_spec(plugin) is None
    ]

    if still_missing:
        raise RuntimeError(
            f"Unable to install QUARK plugins: {', '.join(still_missing)}"
        )


if _QUARK_AVAILABLE:

    class QUARKBenchmarkPipeline(BenchmarkPipeline):
        """Run a QUARK pipeline from an opaque QUARK config file or dict."""

        origin = "core"
        source = "quark"
        name = "workflow"

        def __init__(self, context: RunContext):
            super().__init__(context)
            quark_config = context.params.get("quark_config")
            if quark_config is None:
                raise ValueError(
                    "QUARK benchmark params must include 'quark_config' "
                    "(file path)."
                )
            self.quark_config = quark_config

        def get_category(self) -> str:
            return BenchmarkCategory.APPLICATION

        def run(self) -> PipelineResult:
            parsed = _parse_quark_config(self.quark_config)
            # TODO: consider adding a cli explicit flag, like --install-plugins for this
            ensure_plugins_installed(parsed.plugins)
            load_plugins(parsed.plugins)

            tree_results = [
                run_pipeline_tree(tree) for tree in parsed.pipeline_trees
            ]
            tree_metrics = [_metrics_from_tree_run(result) for result in tree_results]

            status = (
                BenchmarkRunStatus.FAILED if any(isinstance(r, InterruptedTreeRun) for r in tree_results)
                else BenchmarkRunStatus.COMPLETED
            )
            return _base_pipeline_result(self.context, status, _merge_tree_metrics(tree_metrics))

else:
    QUARKBenchmarkPipeline = None  # type: ignore[misc, assignment]
