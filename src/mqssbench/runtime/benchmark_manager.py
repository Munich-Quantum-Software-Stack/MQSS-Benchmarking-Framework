# FILE: mqssbench/runtime/benchmark_manager.py
from typing import Dict, List
import logging
import os
from ..framework import BenchmarkRegistry
from ..framework import ProviderRegistry
from ..framework import AdapterRegistry
from .benchmark_runner import BenchmarkRunner
from ..framework.checkpoint import CheckpointedRunError
from ..framework.types import PipelineResult
from mqssbench.plugins import load_plugins

logger = logging.getLogger(__name__)

# Load built-in and installed plugins
load_plugins()

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

    def dispatch(self) -> List[PipelineResult]:
        """
        Run one or more benchmarks and return a list of PipelineResult objects.
        """
        self._validate_config()

        # Disable interactive plotting for multi-benchmark runs
        os.environ["MQSSBENCH_DISPLAY"] = "0" if isinstance(self.config, list) and len(self.config) > 1 else "1"

        # Normalize to a list of benchmark configs. A bare dict is a single
        # benchmark, not a batch - failures there propagate as before. A list
        # is a batch: isolate failures per-entry so one bad run doesn't cost
        # the rest their (already-independent, already-persisted) results.
        is_batch = isinstance(self.config, list)
        bench_list = self.config if is_batch else [self.config]

        results: List[PipelineResult] = []
        failures: List[tuple[int, CheckpointedRunError]] = []
        for idx, conf in enumerate(bench_list):
            if not isinstance(conf, dict):
                raise TypeError("Each benchmark config must be a dict")
            runner = BenchmarkRunner(conf)
            if is_batch:
                try:
                    result = runner.run()
                except CheckpointedRunError as exc:
                    logger.error("Benchmark %d/%d failed: %s", idx + 1, len(bench_list), exc)
                    failures.append((idx, exc))
                    continue
            else:
                result = runner.run()
            results.append(result)

        if failures:
            summary = "\n".join(f"  [{idx}] {exc}" for idx, exc in failures)
            logger.warning(
                "%d of %d benchmark(s) failed and were checkpointed:\n%s",
                len(failures), len(bench_list), summary,
            )

        return results
