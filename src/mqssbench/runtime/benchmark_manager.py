# FILE: mqssbench/runtime/benchmark_manager.py
from typing import Dict, List
import os
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
        """
        Accept either:
          - a single benchmark config dict (legacy/single)
          - or a list of full benchmark config dicts

        Each entry must be a complete config that the runner understands.
        Validation and more default config will be added later.
        """
        self.config = config

    def _validate_config(self) -> None:
        """Placeholder for future validation."""
        # implement validation logic (with pydantic, jsonschema or similar)
        return

    def dispatch(self) -> List[BenchmarkResult]:
        """
        Run one or more benchmarks and return a list of BenchmarkResult objects.
        """
        self._validate_config()

        # Disable interactive plotting for multi-benchmark runs
        os.environ["MQSSBENCH_DISPLAY"] = "0" if isinstance(self.config, list) and len(self.config) > 1 else "1"

        # Normalize to a list of benchmark configs
        if isinstance(self.config, list):
            bench_list = self.config
        else:
            bench_list = [self.config]

        results: List[BenchmarkResult] = []
        for conf in bench_list:
            if not isinstance(conf, dict):
                raise TypeError("Each benchmark config must be a dict")
            runner = BenchmarkRunner(conf)
            result = runner.run()
            results.append(result)

        return results
