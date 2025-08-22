import pennylane as qml
import numpy as np

def get_hw_circuit(name: str):
    if name == "RB":
        return randomized_benchmarking_circuit(qml.device("default.qubit", wires=2))
    raise ValueError(f"Unsupported HW benchmark: {name}")


def randomized_benchmarking_circuit(device: str = "default.qubit"):

    J = 0.5  # Interaction strength
    h = 0.2  # Transverse field strength
    coeffs = [-J, -h, -h]  # TFIM with 2 sites
    obs = [
        qml.PauliZ(0) @ qml.PauliZ(1),  # Ising interaction between sites 0 and 1
        qml.PauliX(0),
        qml.PauliX(1),
    ]

    hamiltonian = qml.Hamiltonian(coeffs, obs)

    @qml.qnode(device)
    def circuit():
        # TODO1: Example circuit — replace with real RB

        qml.RX(np.pi / 2, wires=0)
        qml.CNOT(wires=[0, 1])

        return qml.expval(qml.PauliZ(0))

    return circuit
