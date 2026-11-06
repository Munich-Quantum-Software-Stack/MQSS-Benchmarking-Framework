"""Tests for checkpoint/resume behavior in the benchmark executors.

Uses fake in-memory adapters/generators rather than the registries, since
these executors only depend on the ``DeviceAdapter``/``CircuitGenerator``
interfaces via ``RunContext``.
"""

from typing import Optional

import pytest

from mqssbench.framework.adapter import DeviceAdapter
from mqssbench.framework.benchmark_executor import DefaultBenchmarkExecutor, HybridBenchmarkExecutor
from mqssbench.framework.checkpoint import (
    CheckpointedRunError,
    CheckpointState,
    checkpoint_path_for,
    load_checkpoint,
)
from mqssbench.framework.circuit_generator import CircuitGenerator
from mqssbench.framework.types import BenchmarkRunStatus, CircuitSpec, ExecutionResult, RunContext


class FailOnCallAdapter(DeviceAdapter):
    """Adapter that raises on a specific 1-indexed call, then always succeeds."""

    name = "fail_on_call_adapter"

    def __init__(self, adapter_params=None, fail_on: Optional[int] = None):
        self.calls = 0
        self.fail_on = fail_on

    @classmethod
    def validate_profiling_config(cls, profiling_config):
        return None

    def get_backend_name(self) -> str:
        return "fail-on-call"

    def execute_circuit(self, context, circuit, num_qubits=None, transpile_mode=True) -> ExecutionResult:
        self.calls += 1
        if self.calls == self.fail_on:
            raise RuntimeError("job submission failed")
        return ExecutionResult(job_id=f"job-{self.calls}", counts={"0": self.calls})


def make_context(run_dir, adapter, params=None, resume_state: Optional[CheckpointState] = None) -> RunContext:
    return RunContext(
        run_id="run-1",
        run_dir=str(run_dir),
        adapter=adapter,
        benchmark_key="core/tests/checkpoint",
        params=params or {},
        metadata={"raw_config": {"benchmark": "core/tests/checkpoint"}},
        checkpoint_path=str(checkpoint_path_for(str(run_dir))),
        resume_state=resume_state,
    )


def test_default_executor_checkpoints_on_failure_and_resumes(tmp_path):
    circuits = [
        CircuitSpec(circuit=(lambda i=i: f"circuit-{i}"), metadata={"num_qubits": 1})
        for i in range(3)
    ]

    adapter = FailOnCallAdapter(fail_on=2)
    context = make_context(tmp_path, adapter)

    with pytest.raises(CheckpointedRunError) as exc_info:
        DefaultBenchmarkExecutor(context).run(circuits, context)

    checkpoint_file = checkpoint_path_for(str(tmp_path))
    assert checkpoint_file.exists()
    assert exc_info.value.checkpoint_path == str(checkpoint_file)

    state = load_checkpoint(checkpoint_file)
    assert state.status == BenchmarkRunStatus.FAILED
    assert state.next_circuit_index == 1
    assert len(state.completed_results) == 1

    # Resume with a working adapter: only the two remaining circuits should run.
    resume_adapter = FailOnCallAdapter(fail_on=None)
    resumed_context = make_context(tmp_path, resume_adapter, resume_state=state)
    results = DefaultBenchmarkExecutor(resumed_context).run(circuits, resumed_context)

    assert len(results) == 3
    assert resume_adapter.calls == 2

    final_state = load_checkpoint(checkpoint_file)
    assert final_state.status == BenchmarkRunStatus.COMPLETED


def test_default_executor_no_checkpoint_when_path_missing(tmp_path):
    circuits = [CircuitSpec(circuit=lambda: "c", metadata={"num_qubits": 1})]
    adapter = FailOnCallAdapter(fail_on=1)
    context = RunContext(
        run_id="run-1",
        run_dir=str(tmp_path),
        adapter=adapter,
        benchmark_key="core/tests/checkpoint",
    )

    with pytest.raises(RuntimeError):
        DefaultBenchmarkExecutor(context).run(circuits, context)

    assert not checkpoint_path_for(str(tmp_path)).exists()


class OneCircuitPerIterationGenerator(CircuitGenerator):
    """Generates exactly one circuit per objective() call; cost depends only on x."""

    def __init__(self, context):
        super().__init__(context)

    def generate(self, params):
        x = list(params["parameters"])

        def builder():
            return f"circuit-for-{x}"

        return [
            CircuitSpec(
                circuit=builder,
                metadata={
                    "num_qubits": 1,
                    "cost_fn": lambda counts, x=x: sum(x),
                },
            )
        ]


def test_hybrid_executor_checkpoints_on_failure_and_resumes(tmp_path):
    adapter = FailOnCallAdapter(fail_on=3)
    params = {"parameters": [0.5, 0.5]}
    context = make_context(tmp_path, adapter, params=params)
    generator = OneCircuitPerIterationGenerator(context)

    with pytest.raises(CheckpointedRunError):
        HybridBenchmarkExecutor(context).run(generator, context)

    checkpoint_file = checkpoint_path_for(str(tmp_path))
    state = load_checkpoint(checkpoint_file)
    assert state.status == BenchmarkRunStatus.FAILED
    assert state.iteration == 2
    assert len(state.completed_results) == 2
    assert state.last_params is not None

    # Resume with a working adapter: run should complete without raising.
    resume_adapter = FailOnCallAdapter(fail_on=None)
    resumed_params = {"parameters": [0.5, 0.5]}
    resumed_context = make_context(tmp_path, resume_adapter, params=resumed_params, resume_state=state)
    resumed_generator = OneCircuitPerIterationGenerator(resumed_context)

    results = HybridBenchmarkExecutor(resumed_context).run(resumed_generator, resumed_context)

    assert len(results) == 1
    assert len(resumed_context.params["expval"]) >= state.iteration

    final_state = load_checkpoint(checkpoint_file)
    assert final_state.status == BenchmarkRunStatus.COMPLETED
