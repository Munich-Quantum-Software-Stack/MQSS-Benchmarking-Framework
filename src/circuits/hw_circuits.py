def get_hw_circuit(name: str, interface: str = "pennylane"):
    if name == "randomized_benchmarking":
        if interface == "pennylane":
            return randomized_benchmarking_circuit_pennylane
        elif interface == "qiskit":
            return randomized_benchmarking_circuit_qiskit
        else:
            raise ValueError(f"Unsupported interface for HW benchmark: {interface}")
    raise ValueError(f"Unsupported HW benchmark: {name}")


def randomized_benchmarking_circuit_pennylane(device):
    import pennylane as qml
    import numpy as np

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
        return qml.expval(hamiltonian)

    return circuit


def randomized_benchmarking_circuit_qiskit():
    from qiskit import QuantumCircuit

    # TODO1: Example circuit — replace with real RB
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    return circuit
