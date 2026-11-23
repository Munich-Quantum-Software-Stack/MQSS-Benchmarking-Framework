import pytest

from mbf.framework.types import (
    CircuitExecutionResult,
    ProfilingMetrics,
    ReportConfig,
    RunContext,
)
from mbf.library.benchmarks.health import HealthBenchmarkAnalyzer, HealthBenchmarkGenerator


class DummyAdapter:
    name = "qiskit_simulator"

    def get_backend_name(self):
        return "dummy"


def make_context(**params):
    return RunContext(
        run_id="health-test",
        run_dir=".",
        adapter=DummyAdapter(),
        benchmark_key="core/native/health",
        params=params,
        report_config=ReportConfig(),
    )


def make_result(counts):
    return CircuitExecutionResult(
        job_id="job",
        counts=counts,
        profiling_metrics=ProfilingMetrics(),
    )


def test_health_generator_creates_bell_state_measurements():
    circuits = HealthBenchmarkGenerator(make_context()).generate({"num_qubits": 2})

    assert len(circuits) == 1
    assert circuits[0].circuit.num_qubits == 2
    assert circuits[0].circuit.num_clbits == 2
    assert circuits[0].circuit.count_ops()["measure"] == 2


def test_health_analyzer_accepts_correlated_results():
    result = HealthBenchmarkAnalyzer(make_context()).analyze(
        [make_result({"00": 90, "11": 10})],
        make_context(min_correlated_probability=0.8),
    )

    assert result.metrics["healthy"] is True
    assert result.metrics["correlated_probability"] == 1.0


def test_health_analyzer_fails_below_threshold():
    with pytest.raises(RuntimeError, match="Health benchmark failed"):
        HealthBenchmarkAnalyzer(make_context()).analyze(
            [make_result({"00": 70, "01": 30})],
            make_context(min_correlated_probability=0.8),
        )
