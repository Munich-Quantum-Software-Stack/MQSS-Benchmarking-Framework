from typing import Dict, List

from ..framework import BenchmarkRegistry
from ..framework import ProviderRegistry
from ..framework import AdapterRegistry
from .benchmark_runner import BenchmarkRunner
from ..framework.types import BenchmarkResult

class BenchmarkManager:
    @staticmethod
    def get_available_benchmarks() -> List[str]:
        return BenchmarkRegistry.list_benchmarks()

    @staticmethod
    def get_available_benchmarks_by_origin(origin: str) -> List[str]:
        return BenchmarkRegistry.list_benchmarks(origin=origin)
    
    @staticmethod
    def get_available_providers() -> List[str]:
        return ProviderRegistry.list_providers()
    
    @staticmethod
    def get_available_adapters() -> List[str]:
        return AdapterRegistry.list_adapters()

    def __init__(self, config: Dict[str, object]):
        self.config = config

    def _validate_config(self) -> None:
        """Validate benchmark configuration before processing."""
        pass # implement this method once all requirements in config are clear and its format is defined

    def dispatch(self) -> BenchmarkResult:
        """Dispatch benchmark execution after config validation."""
        self._validate_config()
        
        runner = BenchmarkRunner(self.config)
        return runner.run()