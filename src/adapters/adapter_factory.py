from .pennylane_adapter import PennyLaneAdapter

# from .qiskit_adapter import Qiskitadapter


def get_adapter(config):
    interface = config["interface"]
    if interface == "pennylane":
        return PennyLaneAdapter(config)
    elif interface == "qiskit":
        raise NotImplementedError("Qiskit Adapter not implemented yet")
        # return QiskitAdapter(config)
    else:
        raise ValueError(f"Unsupported interface: {interface}")
