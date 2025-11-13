import logging
from typing import List, Dict, Any, override
import pkgutil
from ...framework.provider import (
    MAX_CIRCUITS_PER_PROVIDER,
    CircuitProvider,
)
from ...framework import ProviderRegistry
logger = logging.getLogger(__name__)

@ProviderRegistry.register_provider
class MQTBenchProvider(CircuitProvider):
    name = "mqt_bench"

    def __init__(self):
        self._available = []
        try:
            from mqt.bench.benchmarks import get_available_benchmark_names, get_benchmark_description
            available_circuits = get_available_benchmark_names()
            if len(available_circuits) > MAX_CIRCUITS_PER_PROVIDER:
                raise RuntimeError(f"MQTBenchCircuitProvider: number of available circuits ({len(available_circuits)}) "
                                   f"exceeds maximum allowed ({MAX_CIRCUITS_PER_PROVIDER})")
            for circuit_name in available_circuits:
                self._available.append(circuit_name)
        except ImportError:
            logger.warning("failed to get list from package; using fallback benchmark list")
            FALLBACK_BENCHMARKS = [
                "ae","bmw_quark_cardinality","bmw_quark_copula","bv","cdkm_ripple_carry_adder","dj",
                "draper_qft_adder","full_adder","ghz","graphstate","grover","half_adder","hhl",
                "hrs_cumulative_multiplier","modular_adder","multiplier","qaoa","qft","qftentangled",
                "qnn","qpeexact","qpeinexact","qwalk","randomcircuit","rg_qft_multiplier","shor",
                "vbe_ripple_carry_adder","vqe_real_amp","vqe_su2","vqe_two_local","wstate"
                ]            
            self._available = FALLBACK_BENCHMARKS

    @override
    def list_available(self) -> List[str]:
        return list(self._available)

    @override
    def get_circuit(self, circuit_name: str, params: Dict[str, Any]) -> Any:
        try:
            from mqt.bench import get_benchmark, BenchmarkLevel
        except Exception as exc:
            raise RuntimeError("mqt.bench not importable; install mqt-bench to use this provider") from exc

        level = params["level"]
        num_qubits = int(params["num_qubits"])
        level_enum = BenchmarkLevel[level]

        return get_benchmark(benchmark=circuit_name, level=level_enum, circuit_size=num_qubits)

