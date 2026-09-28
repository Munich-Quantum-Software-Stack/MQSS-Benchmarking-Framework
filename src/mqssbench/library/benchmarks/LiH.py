"""LiH ground-state VQE benchmark using a real, ab-initio qubit Hamiltonian.

The Hamiltonian is built with PySCF (STO-3G) in a minimal 2-electron/2-orbital
active space and mapped to 2 qubits via qiskit-nature's parity mapping with
two-qubit reduction - unlike QAOA's MaxCut cost, it has genuine off-diagonal
(X/Y) terms. Since ``HybridBenchmarkExecutor`` only ever measures one Z-basis
circuit per iteration, each Pauli term gets its own basis-rotated circuit and
the weighted results are summed into a single energy estimate per iteration.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, override

import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit

from ...framework import (
    AnalysisResult,
    Benchmark,
    BenchmarkAnalyzer,
    BenchmarkCategory,
    BenchmarkRegistry,
    CircuitGenerator,
    CircuitSpec,
    ExecutionResult,
    HybridBenchmarkExecutor,
    RunContext,
)
from ...framework.utils import make_output_filepath

# Commonly used LiH bond length (STO-3G) in VQE literature/tutorials.
DEFAULT_BOND_LENGTH_ANGSTROM = 1.5474


@lru_cache(maxsize=8)
def _build_lih_qubit_hamiltonian(bond_length_angstrom: float) -> Tuple[Tuple[str, float], ...]:
    """Build LiH's qubit Hamiltonian: (2e, 2o) active space, STO-3G, parity mapping + 2-qubit reduction.

    qiskit-nature/pyscf are imported lazily (not at module scope) since they
    add roughly a second to import - loading them only when a LiH circuit is
    actually generated keeps CLI startup and benchmark discovery fast for
    everyone who isn't running this benchmark. Results are cached per bond
    length since this is a deterministic, somewhat expensive computation that
    the hybrid executor would otherwise re-run on every optimizer iteration.
    """
    from qiskit_nature.units import DistanceUnit
    from qiskit_nature.second_q.drivers import PySCFDriver
    from qiskit_nature.second_q.mappers import ParityMapper
    from qiskit_nature.second_q.transformers import ActiveSpaceTransformer

    driver = PySCFDriver(
        atom=f"Li 0 0 0; H 0 0 {bond_length_angstrom}",
        basis="sto3g",
        charge=0,
        spin=0,
        unit=DistanceUnit.ANGSTROM,
    )
    problem = ActiveSpaceTransformer(num_electrons=2, num_spatial_orbitals=2).transform(driver.run())

    mapper = ParityMapper(num_particles=problem.num_particles)
    qubit_op = mapper.map(problem.hamiltonian.second_q_op())

    # second_q_op() only carries the active-space electronic energy; nuclear
    # repulsion and the inactive-core energy shift are tracked separately in
    # `constants` and must be folded into the identity term to get real
    # total energies (verified against qiskit-nature's own exact solver).
    constant_shift = float(sum(problem.hamiltonian.constants.values()))
    identity_label = "I" * qubit_op.num_qubits

    terms = [
        (label, coeff.real + constant_shift if label == identity_label else coeff.real)
        for label, coeff in qubit_op.to_list()
    ]
    return tuple(terms)


_PAULI_MATRICES = {
    "I": np.eye(2, dtype=complex),
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}


def _pauli_string_to_matrix(pauli_string: str) -> np.ndarray:
    """Kronecker product of single-qubit Pauli matrices for a Pauli string label."""
    matrix = _PAULI_MATRICES[pauli_string[0]]
    for p in pauli_string[1:]:
        matrix = np.kron(matrix, _PAULI_MATRICES[p])
    return matrix


@lru_cache(maxsize=8)
def _exact_ground_state_energy(bond_length_angstrom: float) -> float:
    """Exact ground-state energy of the qubit Hamiltonian via full diagonalization.

    This is the true reference value (not restricted to the VQE's ansatz), used
    to judge how close the optimizer's found energy gets to the actual minimum.
    Only tractable because the active space is fixed at 2 qubits; would need a
    sparse/iterative eigensolver for larger active spaces.
    """
    terms = _build_lih_qubit_hamiltonian(bond_length_angstrom)
    dim = 2 ** len(terms[0][0])
    hamiltonian = np.zeros((dim, dim), dtype=complex)
    for pauli_string, coefficient in terms:
        hamiltonian += coefficient * _pauli_string_to_matrix(pauli_string)
    return float(np.linalg.eigvalsh(hamiltonian)[0])


def _basis_rotate(qc: QuantumCircuit, pauli_string: str) -> None:
    """Rotate each qubit into the Z-eigenbasis of its Pauli factor (Qiskit's
    little-endian labeling: the rightmost character is qubit 0)."""
    for qubit, p in enumerate(reversed(pauli_string)):
        if p == "X":
            qc.h(qubit)
        elif p == "Y":
            qc.sdg(qubit)
            qc.h(qubit)


def pauli_expectation(counts: dict, pauli_string: str) -> float:
    """Expectation value of a Pauli string from Z-basis counts, after the
    circuit already applied `_basis_rotate` for this same `pauli_string`."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    active_positions = [i for i, p in enumerate(reversed(pauli_string)) if p != "I"]
    acc = 0.0
    for bitstring, count in counts.items():
        bits = bitstring[::-1]
        flips = sum(bits[i] == "1" for i in active_positions)
        acc += (-count if flips % 2 else count)
    return acc / total


def _build_ansatz(num_qubits: int, parameters: List[float]) -> QuantumCircuit:
    """Hardware-efficient ansatz: layers of per-qubit RY followed by a CX ladder."""
    if len(parameters) % num_qubits != 0:
        raise ValueError(
            f"len(parameters) ({len(parameters)}) must be a multiple of num_qubits ({num_qubits})."
        )
    qc = QuantumCircuit(num_qubits, num_qubits)
    for layer_start in range(0, len(parameters), num_qubits):
        layer = parameters[layer_start : layer_start + num_qubits]
        for qubit, theta in enumerate(layer):
            qc.ry(theta, qubit)
        for qubit in range(num_qubits - 1):
            qc.cx(qubit, qubit + 1)
    return qc


class LiHGenerator(CircuitGenerator):
    """Builds one basis-rotated circuit per non-identity Hamiltonian term."""

    def __init__(self, context: RunContext):
        super().__init__(context)
        self._terms: Optional[Tuple[Tuple[str, float], ...]] = None

    @override
    def generate(self, params: Dict[str, Any]) -> List[CircuitSpec]:
        bond_length = float(params.get("bond_length", DEFAULT_BOND_LENGTH_ANGSTROM))
        parameters = list(params["parameters"])

        if self._terms is None:
            self._terms = _build_lih_qubit_hamiltonian(bond_length)

        num_qubits = len(self._terms[0][0])
        identity_label = "I" * num_qubits

        circuits: List[CircuitSpec] = []
        for pauli_string, coefficient in self._terms:
            if pauli_string == identity_label:
                # Purely classical contribution (nuclear repulsion + inactive
                # core energy folded into the identity term) - no circuit to run.
                circuits.append(
                    CircuitSpec(
                        circuit=None,
                        metadata={
                            "num_qubits": num_qubits,
                            "skip_execution": True,
                            "constant_value": coefficient,
                            "parameters": parameters,
                            "bond_length": bond_length,
                        },
                    )
                )
                continue

            qc = _build_ansatz(num_qubits, parameters)
            _basis_rotate(qc, pauli_string)
            qc.measure(range(num_qubits), range(num_qubits))

            circuits.append(
                CircuitSpec(
                    circuit=qc,
                    metadata={
                        "num_qubits": num_qubits,
                        "weight": coefficient,
                        "pauli": pauli_string,
                        "cost_fn": lambda counts, p=pauli_string: pauli_expectation(counts, p),
                        "parameters": parameters,
                        "bond_length": bond_length,
                    },
                )
            )
        return circuits


class LiHAnalyzer(BenchmarkAnalyzer):
    @override
    def analyze(self, execution_results: List[ExecutionResult], context: RunContext) -> AnalysisResult:
        result = execution_results[-1]
        bond_length = float(context.params.get("bond_length", DEFAULT_BOND_LENGTH_ANGSTROM))
        exact_ground_state_energy = _exact_ground_state_energy(bond_length)

        artifacts = {}
        if context.report_config.analysis.visualization.enabled:
            plot_filename = self._plot(
                context.params.get("expval", []), exact_ground_state_energy, context
            )
            if plot_filename:
                artifacts["convergence_plot"] = plot_filename

        return AnalysisResult(
            metrics={
                "vqe_energy_hartree": result.exp_value,
                "ground_state_energy_hartree": exact_ground_state_energy,
                "optimal_parameters": result.optimal_params,
            },
            artifacts=artifacts,
        )

    def _plot(
        self, energies: List[float], ground_state_energy: float, context: RunContext
    ) -> Optional[str]:
        if not energies:
            return None

        backend_name = context.adapter.get_backend_name()
        iterations = range(1, len(energies) + 1)

        plt.figure()
        plt.title(f"LiH VQE energy convergence on {backend_name}" if backend_name else "LiH VQE energy convergence")
        plt.xlabel("Optimizer iteration")
        plt.ylabel("Energy (Hartree)")
        plt.grid(alpha=0.4)
        plt.xticks(list(iterations))
        plt.plot(iterations, energies, marker="o", markersize=3, label="VQE runs")
        plt.axhline(ground_state_energy, linestyle="--", color="firebrick", label="Ground state")
        plt.legend()

        filename = make_output_filepath(context.benchmark_key, context.run_dir, tag="convergence_plot")
        plt.savefig(filename)
        plt.close()
        return filename


class LiHBenchmark(Benchmark):
    origin = "core"
    source = "native"
    name = "lih_vqe"

    generator = LiHGenerator
    executor = HybridBenchmarkExecutor
    analyzer = LiHAnalyzer

    supported_adapters: Tuple[str, ...] = ("mqss_qiskit", "qiskit_simulator")
    category = BenchmarkCategory.ALGORITHM

    @override
    def validate_params(self, params: Dict[str, Any]) -> None:
        if not params:
            raise ValueError(
                f"Parameters must be provided for '{self.registry_key()}' benchmark."
            )
        parameters = params.get("parameters")
        if not parameters or len(parameters) % 2 != 0:
            raise ValueError(
                f"'{self.registry_key()}': 'parameters' must be a non-empty list whose length "
                "is a multiple of 2 (one RY angle per qubit, per ansatz layer)."
            )


def register() -> None:
    """Plugin registration hook."""
    BenchmarkRegistry.register_benchmark(LiHBenchmark)
