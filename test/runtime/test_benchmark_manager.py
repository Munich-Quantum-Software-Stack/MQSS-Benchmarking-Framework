"""Tests for BenchmarkManager.dispatch() batch failure isolation."""

import glob
import os

import pytest

from mqssbench.framework.adapter import DeviceAdapter
from mqssbench.framework.adapter_registry import AdapterRegistry
from mqssbench.framework.benchmark import Benchmark
from mqssbench.framework.benchmark_analyzer import DefaultAnalyzer
from mqssbench.framework.benchmark_executor import DefaultBenchmarkExecutor
from mqssbench.framework.benchmark_registry import BenchmarkRegistry
from mqssbench.framework.checkpoint import CheckpointedRunError
from mqssbench.framework.circuit_generator import CircuitGenerator
from mqssbench.framework.types import BenchmarkCategory, CircuitSpec, ExecutionResult, ProfilingMetrics
from mqssbench.runtime.benchmark_manager import BenchmarkManager


@pytest.fixture(autouse=True)
def isolate_registries():
    BenchmarkRegistry._clear()
    AdapterRegistry._clear()
    try:
        yield
    finally:
        BenchmarkRegistry._clear()
        AdapterRegistry._clear()


@pytest.fixture
def registered_dummy_pipeline():
    @AdapterRegistry.register_adapter
    class MaybeFailingAdapter(DeviceAdapter):
        name = "maybe_failing_adapter"

        def __init__(self, adapter_params):
            self.fail = bool((adapter_params or {}).get("fail"))

        @classmethod
        def validate_profiling_config(cls, profiling_config):
            return None

        def get_backend_name(self) -> str:
            return "maybe-failing"

        def execute_circuit(self, context, circuit, num_qubits=None, transpile_mode=True) -> ExecutionResult:
            if self.fail:
                raise RuntimeError("job submission failed")
            return ExecutionResult(
                job_id="job-1",
                counts={"0": 1},
                profiling_metrics=ProfilingMetrics(params={}),
                metadata={},
            )

    class OneCircuitGenerator(CircuitGenerator):
        def __init__(self, context):
            super().__init__(context)

        def generate(self, params):
            return [CircuitSpec(circuit=(lambda: "c"), metadata={"num_qubits": 1})]

    @BenchmarkRegistry.register_benchmark
    class DispatchIsolationBenchmark(Benchmark):
        origin = "core"
        source = "tests"
        name = "dispatch_isolation"
        generator = OneCircuitGenerator
        executor = DefaultBenchmarkExecutor
        analyzer = DefaultAnalyzer
        supported_adapters = tuple()
        category = BenchmarkCategory.HARDWARE

        def validate_params(self, params):
            return None

    return DispatchIsolationBenchmark.registry_key()


def make_config(bench_key: str, output_dir: str, fail: bool) -> dict:
    return {
        "benchmark": bench_key,
        "benchmark_params": {},
        "adapter": "maybe_failing_adapter",
        "adapter_params": {"fail": fail},
        "profiling": {},
        "output_dir": output_dir,
        "report": {"analysis": {"enabled": False}},
    }


def test_dispatch_isolates_batch_failures(tmp_path, registered_dummy_pipeline):
    bench_key = registered_dummy_pipeline
    ok_dir = str(tmp_path / "ok")
    fail_dir = str(tmp_path / "fail")

    config_list = [
        make_config(bench_key, ok_dir, fail=False),
        make_config(bench_key, fail_dir, fail=True),
        make_config(bench_key, ok_dir, fail=False),
    ]

    results = BenchmarkManager(config_list).dispatch()

    assert len(results) == 2

    checkpoint_files = glob.glob(os.path.join(fail_dir, "*", "checkpoint.json"))
    assert len(checkpoint_files) == 1


def test_dispatch_single_config_failure_propagates(tmp_path, registered_dummy_pipeline):
    bench_key = registered_dummy_pipeline
    config = make_config(bench_key, str(tmp_path / "fail"), fail=True)

    with pytest.raises(CheckpointedRunError):
        BenchmarkManager(config).dispatch()
