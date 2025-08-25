from mqss.pennylane_adapter.device import MQSSPennylaneDevice
from .mqss_adapter import MQSSAdapter
from .config import MQSS_TOKEN


class PennyLaneAdapter(MQSSAdapter):
    def __init__(self, config):
        super().__init__(config)
        self.device = MQSSPennylaneDevice(
            # wires=config["wires"],
            # token=config["credentials"]["mqss_token"],
            # backends=[config["backend"]],
            wires=2,
            token=MQSS_TOKEN,
            backends="QExa20",
        )

    def run_circuit(self, circuit, params=None):
        """Given a PennyLane circuit, run it using the PennylaneAdapter

        Args:
            circuit (qml.qnode): Pennylane Circuit
            params (float, optional): Parameters to the circuit. Defaults to None.

        Returns:
            _type_: _description_
        """
        qnode = circuit(self.device)
        if params is not None:
            return qnode(*params)
        else:
            return qnode()
