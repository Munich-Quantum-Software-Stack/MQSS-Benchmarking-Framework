"""
Test suite for BenchmarkRegistry and its runtime integration.

The feature is still experimental, so this suite currently includes only minimal
tests. As the API stabilizes, it will be expanded with comprehensive coverage.
"""

import threading
import pytest
import tempfile

from mqssbench.framework.benchmark_registry import BenchmarkRegistry
from mqssbench.framework.adapter_registry import AdapterRegistry
from mqssbench.runtime.benchmark_runner import BenchmarkRunner
from mqssbench.framework.benchmark import Benchmark
from mqssbench.framework.circuit_generator import CircuitGenerator
from mqssbench.framework.benchmark_executor import BenchmarkExecutor, DefaultBenchmarkExecutor
from mqssbench.framework.benchmark_analyzer import BenchmarkAnalyzer, DefaultAnalyzer
from mqssbench.framework.types import (
    RunContext,
    ReportConfig,
    ExecutionResult,
    ProfilingMetrics,
    CircuitSpec,
    BenchmarkCategory,
    AnalysisConfig,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def temp_run_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp

@pytest.fixture(autouse=True)
def isolate_registries():
    """Reset registries to avoid cross-test pollution."""
    BenchmarkRegistry._clear()
    AdapterRegistry._clear()

    try:
        yield
    finally:
        # post test reset
        BenchmarkRegistry._clear()
        AdapterRegistry._clear()


def make_minimal_context(adapter_name: str, benchmark_key: str) -> RunContext:
    """Helper to create a minimal RunContext for instantiation tests."""
    class DummyAdapter:
        name = adapter_name

        def get_backend_name(self):
            return "dummy"

    return RunContext(
        run_id="test_run_id",
        run_dir=temp_run_dir,
        adapter=DummyAdapter(),
        benchmark_key=benchmark_key,
        report_config=ReportConfig(),  # use defaults
    )


# -----------------------------------------------------------------------------
# Basic registry tests: registration, lookup, instantiation, validation
# -----------------------------------------------------------------------------

def test_register_and_get_and_instantiate():
    """Register a valid Benchmark subclass, retrieve it, list it, and instantiate it."""

    class DummyGenerator(CircuitGenerator):
        def __init__(self, context):
            super().__init__(context)

        def generate(self, params):
            return []

    class DummyExecutor(BenchmarkExecutor):
        def __init__(self, context):
            super().__init__(context)

        def run(self, circuits, context):
            return []

    class DummyAnalyzer(BenchmarkAnalyzer):
        def __init__(self, context):
            super().__init__(context)

        def analyze(self, execution_results, context):
            return None

    @BenchmarkRegistry.register_benchmark
    class MyTestBenchmark(Benchmark):
        origin = "core"
        source = "tests"
        name = "my_test_bench"
        generator = DummyGenerator
        executor = DummyExecutor
        analyzer = DummyAnalyzer
        supported_adapters = ("dummy_adapter",)
        category = BenchmarkCategory.SOFTWARE

        def validate_params(self, params):
            return None

    key = MyTestBenchmark.registry_key()

    cls = BenchmarkRegistry.get_benchmark_class(key)
    assert cls is MyTestBenchmark

    all_keys = BenchmarkRegistry.list_benchmarks()
    assert key in all_keys

    ctx = make_minimal_context(adapter_name="dummy_adapter", benchmark_key=key)
    inst = BenchmarkRegistry.get_benchmark_instance(key, ctx)
    assert isinstance(inst, MyTestBenchmark)
    assert inst.context is ctx


def test_register_duplicate_raises_value_error():
    """Registering the same benchmark twice should raise ValueError."""

    class G(CircuitGenerator):
        def __init__(self, context):
            super().__init__(context)
        def generate(self, params):
            return []

    class E(BenchmarkExecutor):
        def __init__(self, context):
            super().__init__(context)
        def run(self, circuits, context):
            return []

    class A(BenchmarkAnalyzer):
        def __init__(self, context):
            super().__init__(context)
        def analyze(self, execution_results, context):
            return None

    @BenchmarkRegistry.register_benchmark
    class DupBenchmark(Benchmark):
        origin = "core"
        source = "tests"
        name = "dup_bench"
        generator = G
        executor = E
        analyzer = A
        supported_adapters = ()
        category = BenchmarkCategory.HARDWARE

        def validate_params(self, params):
            return None

    with pytest.raises(ValueError):
        # trying to register same class again should raise ValueError
        BenchmarkRegistry.register_benchmark(DupBenchmark)


def test_get_nonexistent_benchmark_raises_value_error():
    """Requesting a validly-formed but not-registered benchmark key should raise ValueError."""
    with pytest.raises(ValueError):
        BenchmarkRegistry.get_benchmark_class("core/native/this_does_not_exist")


def test_list_by_origin_invalid_origin_raises_value_error():
    """Providing an invalid origin to list_benchmarks should raise ValueError."""
    with pytest.raises(ValueError):
        BenchmarkRegistry.list_benchmarks(origin="not_a_valid_origin")


def test_register_non_benchmark_class_raises_type_error():
    """Passing a class that is not a Benchmark subclass to the decorator should raise TypeError."""
    class NotABenchmark:
        pass

    with pytest.raises(TypeError):
        BenchmarkRegistry.register_benchmark(NotABenchmark)


def test_invalid_benchmark_definition_raises_on_subclassing():
    """
    Defining a Benchmark subclass with an invalid origin should raise ValueError
    during class creation via Benchmark.__init_subclass__ validations.
    """

    class G2(CircuitGenerator):
        def __init__(self, context):
            super().__init__(context)
        def generate(self, params):
            return []

    class E2(BenchmarkExecutor):
        def __init__(self, context):
            super().__init__(context)
        def run(self, circuits, context):
            return []

    class A2(BenchmarkAnalyzer):
        def __init__(self, context):
            super().__init__(context)
        def analyze(self, execution_results, context):
            return None

    with pytest.raises(ValueError):
        class BadOriginBenchmark(Benchmark):
            origin = "invalid_origin"  # not in VALID_ORIGINS
            source = "s"
            name = "n"
            generator = G2
            executor = E2
            analyzer = A2
            supported_adapters = ()
            category = BenchmarkCategory.HARDWARE

            def validate_params(self, params):
                return None


# -----------------------------------------------------------------------------
# End-to-end via registry: minimal adapter, generator, analyzer, and run
# -----------------------------------------------------------------------------

def test_end_to_end_benchmark_run_via_registry():
    """
    Minimal end-to-end: register a fake adapter and a simple benchmark, instantiate
    via BenchmarkRegistry.get_benchmark_instance and call run. Assert basic result
    structure and analyzer output.
    """

    from mqssbench.framework.adapter import DeviceAdapter  # import late for clarity

    @AdapterRegistry.register_adapter
    class DummyAdapter(DeviceAdapter):
        name = "dummy_adapter"

        def __init__(self, adapter_params):
            if adapter_params is None:
                adapter_params = {}
            if not isinstance(adapter_params, dict):
                raise TypeError("adapter_params must be a dict")
            self.adapter_params = adapter_params
            self._calls = []

        @classmethod
        def validate_profiling_config(cls, profiling_config):
            return None

        def get_backend_name(self) -> str:
            return "dummy-backend"

        def execute_circuit(self, context: RunContext, circuit, num_qubits=None, transpile_mode=True) -> ExecutionResult:
            if callable(circuit):
                built = circuit()
            else:
                built = circuit

            self._calls.append({"built": built, "num_qubits": num_qubits})

            return ExecutionResult(
                job_id="dummy_job_id",
                counts={"0": 10, "1": 5},
                profiling_metrics=ProfilingMetrics(params={"dummy_metric": 42}),
                metadata={},  # DefaultBenchmarkExecutor will copy spec.metadata into ExecutionResult.metadata
            )

    class MinimalGenerator(CircuitGenerator):
        def __init__(self, context):
            super().__init__(context)

        def generate(self, params):
            def builder():
                return "built-circuit-object"

            return [CircuitSpec(circuit=builder, metadata={"num_qubits": 1})]

    class MinimalAnalyzer(DefaultAnalyzer):
        pass

    @BenchmarkRegistry.register_benchmark
    class MinimalBenchmark(Benchmark):
        origin = "core"
        source = "tests"
        name = "minimal_e2e"
        generator = MinimalGenerator
        executor = DefaultBenchmarkExecutor
        analyzer = MinimalAnalyzer
        supported_adapters = tuple()  # empty tuple means unrestricted
        category = BenchmarkCategory.HARDWARE

        def validate_params(self, params):
            return None

    key = MinimalBenchmark.registry_key()
    adapter_instance = AdapterRegistry.get_adapter("dummy_adapter", {})

    ctx = RunContext(
        run_id="test_run_id",
        run_dir=temp_run_dir,
        adapter=adapter_instance,
        benchmark_key=key,
        params={},  # no params required
        report_config=ReportConfig(analysis=AnalysisConfig(enabled=True)),
    )

    bench_inst = BenchmarkRegistry.get_benchmark_instance(key, ctx)
    result = bench_inst.run()

    assert result is not None
    assert result.benchmark_key == key
    assert isinstance(result.execution_results, list)
    assert len(result.execution_results) == 1

    ex0 = result.execution_results[0]
    assert isinstance(ex0.counts, dict)
    assert ex0.counts.get("0") == 10
    assert ex0.metadata.get("num_qubits") == 1

    assert result.analysis_result is not None
    assert "total_shots" in result.analysis_result.metrics
    assert result.analysis_result.metrics["total_shots"] == 15
    probs = result.analysis_result.metrics["probabilities"]
    assert pytest.approx(probs["0"]) == 10 / 15
    assert pytest.approx(probs["1"]) == 5 / 15


# -----------------------------------------------------------------------------
# BenchmarkRunner integration: use a config dict and run via BenchmarkRunner
# -----------------------------------------------------------------------------

def test_benchmark_runner_integration(temp_output_dir):
    """
    Validate BenchmarkRunner.run works with a real config dict.
    Registers dummy adapter and benchmark, builds config, calls runner.run.
    """

    from mqssbench.framework.adapter import DeviceAdapter  # late import for clarity

    @AdapterRegistry.register_adapter
    class DummyAdapter(DeviceAdapter):
        name = "dummy_adapter"

        def __init__(self, adapter_params):
            if adapter_params is None:
                adapter_params = {}
            if not isinstance(adapter_params, dict):
                raise TypeError("adapter_params must be a dict")
            self.adapter_params = adapter_params

        @classmethod
        def validate_profiling_config(cls, profiling_config):
            return None

        def get_backend_name(self) -> str:
            return "dummy-backend"

        def execute_circuit(self, context: RunContext, circuit, num_qubits=None, transpile_mode=True) -> ExecutionResult:
            return ExecutionResult(
                job_id="dummy_job_id",
                counts={"0": 2, "1": 3},
                profiling_metrics=ProfilingMetrics(params={"dummy": 1}),
                metadata={},
            )

    class MinimalGenerator(CircuitGenerator):
        def __init__(self, context):
            super().__init__(context)

        def generate(self, params):
            def builder():
                return "dummy-built-circuit"
            return [CircuitSpec(circuit=builder, metadata={"num_qubits": 1})]

    class MinimalAnalyzer(DefaultAnalyzer):
        pass

    @BenchmarkRegistry.register_benchmark
    class RunnerIntegrationBenchmark(Benchmark):
        origin = "core"
        source = "tests"
        name = "runner_integration"
        generator = MinimalGenerator
        executor = DefaultBenchmarkExecutor
        analyzer = MinimalAnalyzer
        supported_adapters = tuple()
        category = BenchmarkCategory.HARDWARE

        def validate_params(self, params):
            return None

    bench_key = RunnerIntegrationBenchmark.registry_key()

    config = {
        "benchmark": bench_key,
        "benchmark_params": {},
        "adapter": "dummy_adapter",
        "adapter_params": {},
        "profiling": {},
        "output_dir": temp_output_dir,  # injected temp dir for the test
        "report": {"analysis": {"enabled": True}},
        # "storage": {
        #     "type": "file",
        #     "file": {"format": "json"},
        # },
    }

    runner = BenchmarkRunner(config)
    result = runner.run()

    assert result is not None
    assert result.benchmark_key == bench_key
    assert isinstance(result.execution_results, list)
    assert len(result.execution_results) == 1
    ex = result.execution_results[0]
    assert ex.counts["0"] == 2
    assert ex.counts["1"] == 3
    assert result.analysis_result is not None
    assert result.analysis_result.metrics["total_shots"] == 5


# -----------------------------------------------------------------------------
# Concurrency tests
# -----------------------------------------------------------------------------

def test_benchmark_registry_concurrent_register():
    """
    Concurrency test: multiple threads attempt to register the same Benchmark subclass.
    The registry must remain consistent and only one registration should succeed.
    """
    class G(CircuitGenerator):
        def __init__(self, context):
            super().__init__(context)
        def generate(self, params):
            return []

    class E(BenchmarkExecutor):
        def __init__(self, context):
            super().__init__(context)
        def run(self, circuits, context):
            return []

    class A(BenchmarkAnalyzer):
        def __init__(self, context):
            super().__init__(context)
        def analyze(self, execution_results, context):
            return None

    class ConcurrentBenchmark(Benchmark):
        origin = "core"
        source = "tests"
        name = "concurrent_bench"
        generator = G
        executor = E
        analyzer = A
        supported_adapters = ()
        category = BenchmarkCategory.SOFTWARE

        def validate_params(self, params):
            return None

    results = []
    lock = threading.Lock()

    def try_register():
        try:
            BenchmarkRegistry.register_benchmark(ConcurrentBenchmark)
            with lock:
                results.append("registered")
        except Exception as exc:
            with lock:
                results.append(type(exc).__name__)

    threads = [threading.Thread(target=try_register) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    registered_count = results.count("registered")
    assert registered_count == 1, f"expected 1 registration, got {registered_count}, results: {results}"

    other_errors = [r for r in results if r != "registered"]
    assert all(e == "ValueError" for e in other_errors)

    all_keys = BenchmarkRegistry.list_benchmarks()
    assert len(all_keys) == 1
    assert all_keys[0] == "core/tests/concurrent_bench"


def test_registry_concurrent_unique_benchmarks():
    """
    Stress test: many threads each define and register a unique Benchmark subclass.
    Verifies that:
    - All expected keys appear exactly once.
    - Ordering is correct.
    - No corruption or missing entries.
    """
    class G(CircuitGenerator):
        def __init__(self, context):
            super().__init__(context)
        def generate(self, params):
            return []

    class E(BenchmarkExecutor):
        def __init__(self, context):
            super().__init__(context)
        def run(self, circuits, context):
            return []

    class A(BenchmarkAnalyzer):
        def __init__(self, context):
            super().__init__(context)
        def analyze(self, execution_results, context):
            return None

    thread_count = 25
    keys_expected = set(f"core/tests/concurrent_bench_{i}" for i in range(thread_count))
    errors = []
    lock = threading.Lock()

    def worker(i: int):
        try:
            name = f"concurrent_bench_{i}"
            cls = type(
                f"Bench_{i}",
                (Benchmark,),
                {
                    "origin": "core",
                    "source": "tests",
                    "name": name,
                    "generator": G,
                    "executor": E,
                    "analyzer": A,
                    "supported_adapters": (),
                    "category": BenchmarkCategory.SOFTWARE,
                    "validate_params": lambda self, p: None,
                },
            )
            BenchmarkRegistry.register_benchmark(cls)
        except Exception as exc:
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"unexpected errors: {errors}"

    keys = BenchmarkRegistry.list_benchmarks()
    assert len(keys) == thread_count, f"registry count mismatch: {len(keys)} != {thread_count}"
    assert set(keys) == keys_expected
    assert keys == sorted(keys_expected)
