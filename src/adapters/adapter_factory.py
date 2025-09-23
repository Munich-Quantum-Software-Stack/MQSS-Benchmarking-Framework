from .pennylane_adapter import PennyLaneAdapter
from .qiskit_adapter import QiskitAdapter


def get_adapter(config):
    interface = config["interface"]
    if interface == "pennylane":
        return PennyLaneAdapter(config)
    elif interface == "qiskit":
        return QiskitAdapter(config)
    else:
        raise ValueError(f"Unsupported interface: {interface}")
