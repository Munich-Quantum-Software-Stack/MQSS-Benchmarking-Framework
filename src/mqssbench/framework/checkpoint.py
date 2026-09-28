"""Checkpoint persistence for resumable benchmark runs.

A checkpoint captures enough state to resume a benchmark run after a
mid-run failure (e.g. a job submission error): the original config, the
run's identity (``run_id``/``run_dir``), which circuits/iterations already
produced results, and those results themselves.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .types import BenchmarkRunStatus, ExecutionResult, ProfilingMetrics
from .utils import atomic_write

CHECKPOINT_KIND = "mqssbench_checkpoint"
CHECKPOINT_SCHEMA_VERSION = "1.0"


@dataclass
class CheckpointState:
    """Serializable snapshot of an in-progress or failed benchmark run."""

    kind: str = CHECKPOINT_KIND
    schema_version: str = CHECKPOINT_SCHEMA_VERSION
    run_id: str = ""
    run_dir: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    status: BenchmarkRunStatus = BenchmarkRunStatus.PENDING
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    # DefaultBenchmarkExecutor progress
    next_circuit_index: int = 0

    # HybridBenchmarkExecutor progress
    iteration: int = 0
    last_params: Optional[List[float]] = None
    total_maxiter: int = 0
    iteration_times: List[float] = field(default_factory=list)
    computation_times: List[float] = field(default_factory=list)
    execution_start_times: List[str] = field(default_factory=list)
    execution_end_times: List[str] = field(default_factory=list)
    expval_history: List[float] = field(default_factory=list)

    # Completed ExecutionResults so far, shared by both executors.
    completed_results: List[Dict[str, Any]] = field(default_factory=list)


class CheckpointedRunError(RuntimeError):
    """Raised when a run fails after its progress was saved to a checkpoint."""

    def __init__(self, checkpoint_path: str, original_exception: BaseException):
        super().__init__(
            f"Benchmark run failed; progress was saved. Resume with: "
            f"mqssbench run -c {checkpoint_path}\nOriginal error: {original_exception}"
        )
        self.checkpoint_path = checkpoint_path
        self.original_exception = original_exception


def execution_result_to_dict(result: ExecutionResult) -> Dict[str, Any]:
    """Serialize an ``ExecutionResult`` to a JSON-safe dict."""
    return asdict(result)


def execution_result_from_dict(data: Dict[str, Any]) -> ExecutionResult:
    """Reconstruct an ``ExecutionResult`` from ``execution_result_to_dict`` output."""
    profiling_metrics = data.get("profiling_metrics") or {}
    return ExecutionResult(
        job_id=data["job_id"],
        counts=data["counts"],
        profiling_metrics=ProfilingMetrics(**profiling_metrics),
        metadata=data.get("metadata", {}),
        exp_value=data.get("exp_value"),
        optimal_params=data.get("optimal_params"),
        circuit_depth=data.get("circuit_depth"),
    )


def checkpoint_path_for(run_dir: str) -> Path:
    """Return the standard checkpoint file location for a run directory."""
    return Path(run_dir) / "checkpoint.json"


def save_checkpoint(state: CheckpointState) -> str:
    """Atomically write ``state`` to its run directory's checkpoint file."""
    now = datetime.utcnow().isoformat() + "Z"
    state.updated_at = now
    if not state.created_at:
        state.created_at = now

    path = checkpoint_path_for(state.run_dir)
    payload = asdict(state)
    atomic_write(path, lambda f: json.dump(payload, f, indent=2, ensure_ascii=False))
    return str(path)


def load_checkpoint(path: Union[str, Path]) -> CheckpointState:
    """Load a ``CheckpointState`` from a checkpoint file or its run directory."""
    resolved = _resolve_checkpoint_file(path)
    if resolved is None or not resolved.is_file():
        raise FileNotFoundError(f"No checkpoint found at: {path}")

    with open(resolved, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("kind") != CHECKPOINT_KIND:
        raise ValueError(f"File at {resolved} is not a valid mqssbench checkpoint.")

    data["status"] = BenchmarkRunStatus(data["status"])
    return CheckpointState(**data)


def is_checkpoint_file(path: Union[str, Path]) -> bool:
    """Best-effort sniff: does ``path`` (a file or a run directory) hold a checkpoint?"""
    resolved = _resolve_checkpoint_file(path)
    if resolved is None or not resolved.is_file():
        return False

    try:
        with open(resolved, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return False

    return isinstance(data, dict) and data.get("kind") == CHECKPOINT_KIND


def _resolve_checkpoint_file(path: Union[str, Path]) -> Optional[Path]:
    p = Path(path)
    if p.is_dir():
        return checkpoint_path_for(str(p))
    if p.exists():
        return p
    return None
