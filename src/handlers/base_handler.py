from abc import ABC, abstractmethod


class BenchmarkHandler(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def run(self):
        """Execute the benchmark."""
        pass
        # TODO: To be implemented by the child classes

    @abstractmethod
    def build_circuit(self):
        """Construct circuit or setup logic."""
        pass
        # TODO: To be implemented by the child classes
