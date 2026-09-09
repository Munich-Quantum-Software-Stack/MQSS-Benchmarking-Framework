import json
from datetime import datetime
from pathlib import Path
from ..framework.types import (
    CircuitExecutionResult,
    PipelineEngineExecutionResult,
    PipelineResult,
    RunContext,
)
from .storage_registry import register_storage
from .storage_backend import StorageBackend, StorageError
from ..framework.utils import atomic_write


@register_storage("file")
class FileStorage(StorageBackend):
    def initialize(self):
        self.results_path = Path(self.context.run_dir) / "results.json"
        self.results_path.parent.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: PipelineResult) -> str:
        try:
            if self.config.file.format != "json":
                raise StorageError(f"Unsupported format: {self.config.file.format}")

            payload = serialize_result_json(self.context, result)

            atomic_write(
                self.results_path,
                lambda f: json.dump(payload, f, indent=2, ensure_ascii=False),
            )
        except Exception as e:
            raise StorageError(e)

        return str(self.results_path)

    def close(self):
        return None


def serialize_execution_entry(entry):
    if isinstance(entry, PipelineEngineExecutionResult):
        return {
            "pipeline": entry.pipeline,
            "pipeline_status": entry.pipeline_status,
            "payload": entry.payload,
        }

    if isinstance(entry, CircuitExecutionResult):
        er = entry
        return {
            "job_id": er.job_id,
            "counts": er.counts,
            "metadata": er.metadata or None,
            "profiling_metrics": (
                er.profiling_metrics.params if er.profiling_metrics else None
            ),
            "exp_value": er.exp_value if er.exp_value is not None else None,
            "optimal_params": (
                er.optimal_params if er.optimal_params is not None else None
            ),
            "iteration_duration": (
                er.profiling_metrics.iteration_duration
                if er.profiling_metrics.iteration_duration is not None
                else None
            ),
            "multiple_execution_duration": (
                er.profiling_metrics.multiple_execution_duration
                if er.profiling_metrics.multiple_execution_duration is not None
                else None
            ),
            "execution_start_times": (
                er.profiling_metrics.execution_start_times
                if er.profiling_metrics.execution_start_times is not None
                else None
            ),
            "execution_end_times": (
                er.profiling_metrics.execution_end_times
                if er.profiling_metrics.execution_end_times is not None
                else None
            ),
        }

    return entry


def serialize_result_json(context: RunContext, result: PipelineResult) -> dict:
    now = datetime.utcnow().isoformat() + "Z"


    return {
        "schema_version": 0.1,
        "timestamp_utc": now,
        "run_id": context.run_id,
        "benchmark_key": result.benchmark_key,
        "category": result.category,
        "status": result.status,
        "benchmark_params": result.params,
        "adapter": {"backend": context.adapter.get_backend_name()},
        "execution_results": [
            serialize_execution_entry(entry) for entry in result.execution_results
        ],
        "analysis": (
            {
                "metrics": result.analysis_result.metrics,
                "artifacts": result.analysis_result.artifacts,
            }
            if result.analysis_result
            else None
        ),
    }
