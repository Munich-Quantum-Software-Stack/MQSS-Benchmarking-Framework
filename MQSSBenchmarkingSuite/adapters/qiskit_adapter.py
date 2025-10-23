from ..adapters.mqss_adapter import MQSSAdapter
from mqss.qiskit_adapter import MQSSQiskitAdapter
from ..adapters.config import MQSS_TOKEN, MQSS_BACKEND
from qiskit import transpile


class QiskitAdapter(MQSSAdapter):

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
        self.shots = int(config["shots"]) if config.get("shots") is not None else None

        self.adapter = MQSSQiskitAdapter(token=token)
        self.backend = self.adapter.get_backend(backend_name)


    def run_circuit(self, circuit, circuit_params=None, transpile_mode=True):
        """Given a Qiskit circuit, run it using the QiskitAdapter

        Args:
            circuit (callable): A builder function returning a `QuantumCircuit`.
            circuit_params (optional): parameters to the circuit. Defaults to None.

        Returns:
            dict: Dictionary of measurement counts from the executed circuit.
        """
        # Build circuit: support factory functions receiving circuit_params dict
        if callable(circuit):
            if isinstance(circuit_params, dict):
                built_circuit = circuit(**circuit_params)
            elif circuit_params is None:
                built_circuit = circuit()
            else:
                built_circuit = circuit(circuit_params)
        else:
            built_circuit = circuit
        
        # print for debugging. TODO: later we can define a verbose mode
        print(f"Circuit:\n{built_circuit}")
        print("Running the circuit ...")

        # Transpile to basic gates to avoid unsupported custom instructions errors (a conservative basis set compatible with most backends)
        if transpile_mode is True:
            built_circuit = transpile(
                built_circuit,
                basis_gates=["u", "cx"],
                optimization_level=0,
            )

        if self.shots is not None: 
            job = self.backend.run(built_circuit, shots=self.shots)
        else:
            job = self.backend.run(built_circuit)
        return job.result().get_counts()

    # TODO: add ability to use batch circuits running for efficiency
    # def run_circuits(self, circuits, circuits_params=None):

    # TODO: consider exploring alternative solutions for transpilation here