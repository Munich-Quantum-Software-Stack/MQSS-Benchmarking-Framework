from typing import Any, Dict, List, Tuple, override
import logging
import numpy as np

from ...framework import (
    Benchmark,
    BenchmarkAnalyzer,
    BenchmarkCategory,
    CircuitGenerator,
    CircuitSpec,
    DefaultBenchmarkExecutor,
    RunContext,
    ExecutionResult,
    BenchmarkRegistry,
    AnalysisResult,
)

logger = logging.getLogger(__name__)

class QuantumVolumeGenerator(CircuitGenerator):
    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:
        from qiskit.circuit.library import QuantumVolume

        width = int(params["num_qubits"])
        depth = int(params["depth"])
        trials = int(params["trials"])
        circuits: List[CircuitSpec] = []
        for trial_index in range(trials):
            seed = 42 + trial_index
            circuit = QuantumVolume(width, depth, seed=seed)
            circuit.measure_all()
            circuits.append(
                CircuitSpec(
                    circuit=circuit,
                    metadata={"num_qubits": width, "seed": seed, "width": width, "depth": depth},
                )
            )
        return circuits


class QuantumVolumeAnalyzer(BenchmarkAnalyzer):
    @override
    def analyze(self, execution_results: List[ExecutionResult], context: RunContext) -> AnalysisResult:
        from qiskit.circuit.library import QuantumVolume
        from qiskit.quantum_info import Statevector

        width = int(context.params["num_qubits"])
        depth = int(context.params["depth"])
        p_heavy_list: List[float] = []

        for result in execution_results:
            seed = int(result.metadata["seed"])
            counts = result.counts
            ideal_circuit = QuantumVolume(width, depth, seed=seed)
            probabilities = np.abs(Statevector.from_instruction(ideal_circuit).data) ** 2
            median_probability = float(np.median(probabilities))
            heavy_outcomes = {idx for idx, value in enumerate(probabilities) if value > median_probability}
            total = sum(counts.values())
            if total == 0:
                raise ValueError("Quantum Volume analysis failed: zero total counts encountered.")
            heavy_probability = sum(v for k, v in counts.items() if int(k, 2) in heavy_outcomes) / total
            p_heavy_list.append(float(heavy_probability))

        if not p_heavy_list:
            raise ValueError("Quantum Volume analysis failed: no heavy outcome data found.")

        median_p_heavy = float(np.median(p_heavy_list))
        passed_threshold = bool(median_p_heavy >= 2 / 3)

        if context.report_config.analysis.visualization.enabled:
            logger.warning("Visualization for '%s' is not implemented.", context.benchmark_key)

        return AnalysisResult(
            metrics={
                "trials_p_heavy": p_heavy_list,
                "median_p_heavy": median_p_heavy,
                "passed_threshold": passed_threshold,
            },
            artifacts={},
        )

class QuantumVolumeBenchmark(Benchmark):
    origin = "core"
    source = "native"
    name = "quantum_volume"
    generator = QuantumVolumeGenerator
    executor = DefaultBenchmarkExecutor
    analyzer = QuantumVolumeAnalyzer
    supported_adapters: Tuple[str, ...] = ("mqss_qiskit",)
    category = BenchmarkCategory.HARDWARE
    
    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        if not params:
            raise ValueError(f"Parameters must be provided for '{self.registry_key()}' benchmark.")
        required_params = ["num_qubits", "depth", "trials"]
        missing = [field for field in required_params if field not in params]
        if missing:
            raise ValueError(f"Missing required parameters for '{self.registry_key()}': {missing}")
        return None


def register() -> None:
    """Plugin registration hook."""
    BenchmarkRegistry.register_benchmark(QuantumVolumeBenchmark)