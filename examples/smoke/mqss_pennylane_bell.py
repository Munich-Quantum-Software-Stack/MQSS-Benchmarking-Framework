"""Minimal Bell-state benchmark for manual PennyLane adapter smoke checks."""

from typing import Any, Dict, List, Tuple, override

import pennylane as qml

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
        def build(device):
            @qml.qnode(device)
            def circuit():
                qml.Hadamard(wires=0)
                qml.CNOT(wires=[0, 1])
                return qml.counts(wires=[0, 1])

            return circuit

        return [CircuitSpec(circuit=build, metadata={"num_qubits": 2})]


@BenchmarkRegistry.register_benchmark
class PennyLaneBellBenchmark(Benchmark):
    origin = "user"
    source = "smoke"
    name = "pennylane_bell"

    generator = BellStateGenerator
    executor = DefaultBenchmarkExecutor
    analyzer = DefaultAnalyzer

    supported_adapters: Tuple[str, ...] = ("mqss_pennylane",)
    category = BenchmarkCategory.SOFTWARE

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        pass


SMOKE_CONFIG = {
    "benchmark": PennyLaneBellBenchmark.registry_key(),
    "benchmark_params": {},
    "adapter": "mqss_pennylane",
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
