"""Minimal Bell-state benchmark for manual Qiskit adapter smoke checks."""

from typing import Any, Dict, List, Tuple, override

from qiskit import QuantumCircuit

from mqssbench.framework import (
    Benchmark,
    BenchmarkCategory,
    BenchmarkRegistry,
    CircuitGenerator,
    CircuitSpec,
    DefaultAnalyzer,
    DefaultBenchmarkExecutor,
)


class BellStateGenerator(CircuitGenerator):
    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        return [CircuitSpec(circuit=qc, metadata={"num_qubits": 2})]


@BenchmarkRegistry.register_benchmark
class QiskitBellBenchmark(Benchmark):
    origin = "user"
    source = "smoke"
    name = "qiskit_bell"

    generator = BellStateGenerator
    executor = DefaultBenchmarkExecutor
    analyzer = DefaultAnalyzer

    supported_adapters: Tuple[str, ...] = ("mqss_qiskit",)
    category = BenchmarkCategory.SOFTWARE

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        pass


SMOKE_CONFIG = {
    "benchmark": QiskitBellBenchmark.registry_key(),
    "benchmark_params": {},
    "adapter": "mqss_qiskit",
    "adapter_params": {
        "backend": "QExa20",
        "backend_params": {},
        "credentials": {"mqss_token": ""},
        "shots": 200,
    },
    "output_dir": "./results",
    "report": {
        "analysis": {
            "enabled": True,
            "visualization": {
                "enabled": False,
                "show": False,
            },
        },
    },
    "storage": {
        "enabled": True,
        "type": "file",
        "file": {"format": "json"},
    },
}
