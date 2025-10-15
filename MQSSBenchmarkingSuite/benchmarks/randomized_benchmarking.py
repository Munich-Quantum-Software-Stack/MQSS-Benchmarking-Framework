from .benchmark import Benchmark
from .registry import register_benchmark


class RandomizedBenchmarkingBenchmark(Benchmark):

    @classmethod
    def name(self) -> str:
        return "randomized_benchmarking"

    @classmethod
    def interfaces(self) -> list:
        return ["qiskit"]

    @classmethod
    def validate_params(self, params: dict) -> dict:
        p = dict(params or {})
        p.setdefault("num_qubits", 1)
        p.setdefault("lengths", [2, 4, 8, 16])
        p.setdefault("num_sequences", 2)
        return p

    @classmethod
    def check_requirements(self, interface: str) -> None:
        if interface not in self.interfaces():
            raise ValueError(f"Only {self.interfaces()} interface(s) are supported for {self.name()} currently")

    @classmethod
    def execute(self, adapter, params: dict):
        from qiskit_experiments.library.randomized_benchmarking import StandardRB

        lengths = params["lengths"]
        num_qubits = int(params["num_qubits"])
        num_sequences = int(params["num_sequences"])

        runs = {}
        for L in lengths:
            exp = StandardRB(
                physical_qubits=list(range(num_qubits)),
                lengths=[L],
                num_samples=num_sequences,
                seed=42,
            )
            seq_counts = []
            exp_circuits = exp.circuits()
            for circ in exp_circuits:
                counts = adapter.run_circuit(lambda: circ)
                seq_counts.append(counts)
            runs[L] = seq_counts
        return runs

    @classmethod
    def analyze(self, params: dict, runs) -> dict:
        num_qubits = int(params["num_qubits"])
        status = "failed"
        mean_survivals = []
        p_decay = float("nan")
        avg_gate_error = float("nan")

        result = self.rb_analyze(num_qubits, runs)
        if result is None:
            print("Randomized Benchmarking analysis failed.")
        else:
            status = "success"
            mean_survivals, p_decay, avg_gate_error = result

        return {
            "num_qubits": num_qubits,
            "lengths": sorted(runs.keys()),
            "num_sequences": int(params["num_sequences"]),
            "mean_survivals": mean_survivals,
            "decay_p": p_decay,
            "avg_gate_error": avg_gate_error,
            "status": status,
            "runs_info": runs,
        }


    @classmethod
    def rb_analyze(self, num_qubits, runs):
        import numpy as np
        from scipy.optimize import curve_fit

        mean_survivals = []

        try:
            # Find mean survival probabilities for each sequence length
            lengths = sorted(runs.keys())
            for L in lengths:
                seq_counts = runs[L]
                zero_state = "0" * num_qubits
                survivals = [] 
                for counts in seq_counts:
                    total = sum(counts.values())
                    if total == 0:
                        return None  # fail: no measurement counts
                    survivals.append(counts.get(zero_state, 0) / total)  # Survival probability is the probability of measuring the all-zero state |00..0>
                if not survivals:
                    return None  # fail: empty survival list
                mean_survivals.append(float(np.mean(survivals)))

            # Fit the mean survival probabilities to an exponential decay model to extract the decay parameter
            def model(L, A, p, B):
                return A * (p ** L) + B  # assuming gate-independent and time-independent errors

            Ls = np.array(lengths, dtype=float)
            ys = np.array(mean_survivals, dtype=float)

            try:
                popt, _ = curve_fit(model, Ls, ys, bounds=([0, 0, 0], [1, 1, 1]))
                _, p_decay, _ = popt
            except Exception:
                return None  # fail: curve fit failed

            # Calculate average gate error
            dimension = 2 ** num_qubits  # Dimension of the Hilbert space for num_qubits qubits
            avg_gate_error = ((dimension - 1) / dimension) * (1 - p_decay)  # Error per Clifford (EPC)

            # TODO: Consider using RBAnalysis instead of manual fitting and calculations above:
            # https://qiskit-community.github.io/qiskit-experiments/stubs/qiskit_experiments.library.randomized_benchmarking.RBAnalysis.html

            return mean_survivals, float(p_decay), float(avg_gate_error)

        except Exception as e:
            print(f"Error in rb_analyze: {e}")
            return None  # fail: unexpected error


register_benchmark(RandomizedBenchmarkingBenchmark)


