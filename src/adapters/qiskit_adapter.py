from src.adapters.mqss_adapter import MQSSAdapter
from mqss.qiskit_adapter import MQSSQiskitAdapter
from src.adapters.config import MQSS_TOKEN


class QiskitAdapter(MQSSAdapter):

    def __init__(self, config):
        super().__init__(config)

        if not isinstance(config, dict):
            raise TypeError("config must be a dict")
        backend_name = str(config.get("backend", "")).strip()
        credentials = config.get("credentials") or {}
        token = (credentials.get("mqss_token") if isinstance(credentials, dict) else None) or MQSS_TOKEN
        if not token:
            raise ValueError("Missing required config: credentials.mqss_token or MQSS_TOKEN")
        if not backend_name:
            raise ValueError("Missing required config: backend")
        self.adapter = MQSSQiskitAdapter(token=token)
        self.backend = self.adapter.get_backend(backend_name)
        self.shots = int(config["shots"]) if config.get("shots") is not None else None
        #TODO: consider using config["wires"], which is number of qubits

    def run_circuit(self, circuit, params=None):
        """Given a Qiskit circuit, run it using the QiskitAdapter

        Args:
            circuit (callable): A builder function returning a `QuantumCircuit`.
            params (float, optional): Parameters to the circuit. Defaults to None.

        Returns:
            _type_: _description_
        """        
        # In current implementation, circuit is expected to be a function, so we call it to get a QuantumCircuit
        if callable(circuit):
            built_circuit = circuit()
        else:
            built_circuit = circuit

        print("Running the circuit ...")  # print for debugging. TODO: later we can define a verbose mode
        if self.shots is not None:
            job = self.backend.run(built_circuit, shots=self.shots)
        else:
            job = self.backend.run(built_circuit)
        return job.result()
