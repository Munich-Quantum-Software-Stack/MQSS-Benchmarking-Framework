from abc import ABC, abstractmethod


class Benchmark(ABC):

    @classmethod
    @abstractmethod
    def name(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def interfaces(self) -> list:
        pass

    @classmethod
    @abstractmethod
    def validate_params(self, params: dict) -> dict:
        pass

    @classmethod
    @abstractmethod
    def check_requirements(self, interface: str) -> None:
        pass

    @classmethod
    @abstractmethod
    def execute(self, adapter, params: dict):
        pass

    # TODO: Consider adding a function for standardization of output of execute (esp. useful for supporting multiple interfaces)

    @classmethod
    @abstractmethod
    def analyze(self, params: dict, runs) -> dict:
        pass
    pass


