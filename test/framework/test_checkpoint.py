import json

import pytest

from mqssbench.framework.checkpoint import (
    CheckpointState,
    checkpoint_path_for,
    is_checkpoint_file,
    load_checkpoint,
    save_checkpoint,
    execution_result_from_dict,
    execution_result_to_dict,
)
from mqssbench.framework.types import BenchmarkRunStatus, ExecutionResult, ProfilingMetrics


def test_execution_result_round_trip():
    result = ExecutionResult(
        job_id="job-1",
        counts={"0": 5, "1": 3},
        profiling_metrics=ProfilingMetrics(params={"transpiler": 1.2}),
        metadata={"num_qubits": 2},
        exp_value=-0.5,
        optimal_params=[0.1, 0.2],
    )

    restored = execution_result_from_dict(execution_result_to_dict(result))

    assert restored == result


def test_save_and_load_checkpoint_round_trip(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    result = ExecutionResult(job_id="job-1", counts={"0": 1})
    state = CheckpointState(
        run_id="run-1",
        run_dir=str(run_dir),
        config={"benchmark": "core/native/qaoa"},
        status=BenchmarkRunStatus.FAILED,
        error="boom",
        next_circuit_index=1,
        completed_results=[execution_result_to_dict(result)],
    )

    path = save_checkpoint(state)
    assert path == str(checkpoint_path_for(str(run_dir)))

    loaded = load_checkpoint(path)
    assert loaded.run_id == "run-1"
    assert loaded.status == BenchmarkRunStatus.FAILED
    assert loaded.error == "boom"
    assert loaded.next_circuit_index == 1
    assert loaded.config == {"benchmark": "core/native/qaoa"}
    assert execution_result_from_dict(loaded.completed_results[0]) == result


def test_load_checkpoint_from_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    save_checkpoint(CheckpointState(run_id="run-1", run_dir=str(run_dir)))

    loaded = load_checkpoint(str(run_dir))
    assert loaded.run_id == "run-1"


def test_load_checkpoint_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_checkpoint(tmp_path / "does_not_exist.json")


def test_load_checkpoint_rejects_non_checkpoint_file(tmp_path):
    path = tmp_path / "not_a_checkpoint.json"
    path.write_text(json.dumps({"foo": "bar"}))

    with pytest.raises(ValueError):
        load_checkpoint(path)


def test_is_checkpoint_file_true_for_checkpoint(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    path = save_checkpoint(CheckpointState(run_id="run-1", run_dir=str(run_dir)))

    assert is_checkpoint_file(path) is True
    assert is_checkpoint_file(str(run_dir)) is True


def test_is_checkpoint_file_false_for_other_files(tmp_path):
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text("benchmark: core/native/qaoa\n")
    assert is_checkpoint_file(yaml_path) is False

    other_json = tmp_path / "results.json"
    other_json.write_text(json.dumps({"schema_version": 0.1}))
    assert is_checkpoint_file(other_json) is False

    empty_dir = tmp_path / "empty_run"
    empty_dir.mkdir()
    assert is_checkpoint_file(empty_dir) is False

    assert is_checkpoint_file(tmp_path / "missing.json") is False
