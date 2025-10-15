from abc import ABC, abstractmethod


class MQSSAdapter(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def run_circuit(self, circuit, circuit_params=None, transpile_mode=True):
        # TODO: To be implemented by the child classes
        pass
