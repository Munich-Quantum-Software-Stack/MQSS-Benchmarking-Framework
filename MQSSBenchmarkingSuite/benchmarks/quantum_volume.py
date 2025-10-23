from typing import Any
from unittest import result
from .benchmark import Benchmark
from .registry import register_benchmark


class QuantumVolumeBenchmark(Benchmark):

    @classmethod
    def name(self) -> str:
        return "quantum_volume"

    @classmethod
    def interfaces(self) -> list:
        return ["qiskit"]

    @classmethod
    def validate_params(self, params: dict) -> dict:
        p = dict(params or {})
        p.setdefault("num_qubits", 2) # width in QV terminology
        p.setdefault("depth", int(p.get("num_qubits")))
        p.setdefault("trials", 5)
        return p

    @classmethod
    def check_requirements(self, interface: str) -> None:
        if interface not in self.interfaces():
            raise ValueError(f"Only {self.interfaces()} interface(s) are supported for {self.name()} currently")

    @classmethod
    def execute(self, adapter, params: dict):
        runs = []
        from qiskit.circuit.library import QuantumVolume
        width = int(params["num_qubits"])
        depth = int(params["depth"])
        trials = int(params["trials"])
        for t in range(trials):
            qc = QuantumVolume(width, depth, seed=42 + t)
            qc.measure_all()
            counts = adapter.run_circuit(lambda: qc)
            runs.append({"seed": 42 + t, "counts": counts})
        return runs

    @classmethod
    def analyze(self, params: dict, runs) -> dict:
        width = int(params["num_qubits"])
        depth = int(params["depth"])
        
        status = "failed"
        p_heavy_list = []
        median_p_heavy = float("nan")
        passed_threshold = False

        result = self.qv_analyze(width, depth, runs)
        if result is None:
            print("Quantum Volume analysis failed.")
        else:
            status = "success"
            p_heavy_list, median_p_heavy, passed_threshold = result
            
        return {
            "width": width,
            "depth": depth,
            "num_trials": params["trials"],
            "trials_p_heavy": p_heavy_list,
            "median_p_heavy": median_p_heavy,
            "passed_threshold": passed_threshold,
            "status": status,
            "runs_info": runs,
        }

    @classmethod
    def qv_analyze(self, width, depth, runs):
        from qiskit.quantum_info import Statevector
        from qiskit.circuit.library import QuantumVolume
        import numpy as np

        median_p_heavy = float("nan")
        passed_threshold = False
        p_heavy_list = []

        try:
            for entry in runs:
                seed = int(entry["seed"]) 
                counts = entry["counts"]
                # Ideal distribution from unmeasured circuit
                ideal_qc = QuantumVolume(width, depth, seed=seed)
                sv = Statevector.from_instruction(ideal_qc)
                # Converts statevector amplitudes to probabilities
                probs = np.abs(sv.data) ** 2
                median = np.median(probs)
                heavy = {i for i, p in enumerate(probs) if p > median}  # find heavy outcomes (those with above median probability)
                total = sum(counts.values())
                if total == 0: 
                    return None  # fail: no measurement counts
                p_heavy = sum(v for k, v in counts.items() if int(k, 2) in heavy) / total  # probability of heavy outcomes
                p_heavy_list.append(float(p_heavy))

            if p_heavy_list:
                median_p_heavy = float(np.median(p_heavy_list))  # finds median heavy probability across trials
                passed_threshold = bool(median_p_heavy >= 2 / 3)  # 2/3 is the success threshold for quantum volume
                return p_heavy_list, median_p_heavy, passed_threshold

            return None  # fail: no valid data

        except Exception as e:
            print(f"Error in qv_analyze: {e}")
            return None  # fail: unexpected error


register_benchmark(QuantumVolumeBenchmark)