from mqss.pennylane_adapter.device import MQSSPennylaneDevice
from .mqss_adapter import MQSSAdapter
from .config import MQSS_TOKEN, MQSS_BACKEND
from typing import override


class PennyLaneAdapter(MQSSAdapter):
    def __init__(self, config):
        super().__init__(config)

        if not isinstance(config, dict):
            raise TypeError("config must be a dict")
        backend_name = str(config.get("backend", "") or MQSS_BACKEND).strip()
        if not backend_name:
            raise ValueError("Missing required config: backend or MQSS_BACKEND")
        credentials = config.get("credentials") or {}
        token = (
            credentials.get("mqss_token") if isinstance(credentials, dict) else None
        ) or MQSS_TOKEN
        if not token:
            raise ValueError(
                "Missing required config: credentials.mqss_token or MQSS_TOKEN"
            )
        shots = int(config["shots"]) if config.get("shots") is not None else None
        num_qubits = self.config["benchmark_params"]["num_qubits"]

        self.device = MQSSPennylaneDevice(
            wires=num_qubits,
            token=token,
            shots=shots,
            backends=backend_name,
        )

    @override
    def run_circuit(self, circuit, circuit_params=None, transpile_mode=True):
        """Given a PennyLane circuit, run it using the PennylaneAdapter

        Args:
            circuit (qml.qnode): Pennylane Circuit
            circuit_params (optional): parameters to the circuit. Defaults to None.

        Returns:
            dict: Dictionary of measurement counts from the executed circuit.
        """
        # print for debugging. TODO: later we can define a verbose mode
        print(f"Circuit:\n{circuit}")
        print("Running the circuit ...")

        # Build qnode, pass device and params dict (if any)
        if callable(circuit):
            if isinstance(circuit_params, dict):
                qnode = circuit(self.device, **circuit_params)
            elif circuit_params is None:
                qnode = circuit(self.device)
            else:
                qnode = circuit(self.device, circuit_params)
        else:
            qnode = circuit

        # Execute the qnode (circuit_params already bound during construction)
        return qnode()
