import pennylane as qml
import numpy as np
import qiskit
from qiskit_experiments.library import StandardRB, InterleavedRB
from qiskit_experiments.framework import ParallelExperiment, BatchExperiment

# --------------------------------------------------------
# Qiskit circuits
# --------------------------------------------------------
def get_hw_circuit_qiskit(name: str):
    if name == "RB":
        return qiskit_rb_circuit()
    else:
        raise ValueError(f"Not yet implemented: {name}")
    
def qiskit_rb_circuit(nqubits=1, length=5, num_samples=5):
    lengths = np.arange(2, length, 2)
    nsamples = num_samples
    seed = 1010
    qubits = [0]
    rb_exp = StandardRB(qubits, lengths, num_samples=nsamples, seed=seed)
    circuits = rb_exp.circuits()
    # print(f"Generated {len(circuits)} circuits for RB benchmark | length={lengths}, num_samples={num_samples}")
    return circuits

# --------------------------------------------------------
# Pennylane circuits
# --------------------------------------------------------

def get_hw_circuit_pennylane(name: str):
    if name == "RB":
        return pennylane_rb_circuit()
    else:
        raise ValueError(f"Not yet implemented: {name}")

def pennylane_rb_circuit():
    J = 0.5  # Interaction strength
    h = 0.2  # Transverse field strength
    coeffs = [-J, -h, -h]  # TFIM with 2 sites
    obs = [
        qml.PauliZ(0) @ qml.PauliZ(1),  # Ising interaction between sites 0 and 1
        qml.PauliX(0),
        qml.PauliX(1),
    ]
    hamiltonian = qml.Hamiltonian(coeffs, obs)

    @qml.qnode(qml.device("default.qubit", wires=2))
    def circuit():
        # TODO1: Example circuit — replace with real RB
        qml.RX(np.pi / 2, wires=0)
        qml.CNOT(wires=[0, 1])
        return qml.expval(qml.PauliZ(0))

    return circuit
