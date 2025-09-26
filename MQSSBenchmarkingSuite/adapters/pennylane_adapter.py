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

        self.device = MQSSPennylaneDevice(
            wires=2,  # TODO: use wires=config["wires"] later
            token=token,
            shots=shots,
            backends=backend_name,
        )

    @override
    def run_circuit(self, circuit, params=None):
        """Given a PennyLane circuit, run it using the PennylaneAdapter

        Args:
            circuit (qml.qnode): Pennylane Circuit
            params (float, optional): Parameters to the circuit. Defaults to None.

        Returns:
            _type_: _description_
        """
        print(
            "Running the circuit ..."
        )  # print for debugging. TODO: later we can define a verbose mode
        print(self.device)
        print(circuit)
        qnode = circuit(self.device)
        if params is not None:
            return qnode(*params)
        else:
            return qnode()
