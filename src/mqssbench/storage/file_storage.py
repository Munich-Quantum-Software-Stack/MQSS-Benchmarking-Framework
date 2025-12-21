import json
import os
from datetime import datetime
from ..framework import RunContext
from ..framework.types import BenchmarkResult

# TODO: this is temporarily here until we have a proper storage component
def save_result_json(context: RunContext, result: BenchmarkResult) -> str:
    run_dir = context.run_dir
    os.makedirs(run_dir, exist_ok=True)
    now = datetime.utcnow().isoformat() + "Z"

    payload = {
        "schema_version": 0.1, # use version 1.0 when becoming stable
        "timestamp_utc": now,
        "run_id": context.run_id,
        "benchmark_key": result.benchmark_key,
        "benchmark_params": result.params,
        "adapter": {
            "backend": context.adapter.get_backend_name()
        },
        "execution_results": [
            {
                "job_id": getattr(er, "job_id", None),
                "counts": er.counts,
                # TODO: write this
                "profiling_metrics": getattr(er.profiling_metrics, "params", None) if getattr(er, "profiling_metrics", None) else None,
                #"metadata": er.metadata,
            } for er in result.execution_results
        ],
        "analysis": {
            "metrics": getattr(result.analysis_result, "metrics", None),
            "artifacts": getattr(result.analysis_result, "artifacts", None),
        } if result.analysis_result else None,
    }

    # Atomic write to avoid corrupted result.json on failure
    tmp = os.path.join(run_dir, ".result.json.tmp")
    final = os.path.join(run_dir, "result.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp, final)

    return final



