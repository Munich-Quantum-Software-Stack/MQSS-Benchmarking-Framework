from typing import Any, Dict

from ..framework import AdapterRegistry
from ..framework import RunContext, BenchmarkRegistry
from ..framework.types import ProfilingConfig, BenchmarkResult, OutputConfig

class BenchmarkRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self) -> BenchmarkResult:
        adapter_name = self.config.get("adapter")
        if not adapter_name:
            raise ValueError("The 'adapter' field is mandatory in the benchmark configuration.")
        adapter = AdapterRegistry.get_adapter(adapter_name, self.config)
        # get and validate benchmark key
        benchmark_key = self._resolve_benchmark_key()
        # validate profiling config
        profiling_config = self.config.get("profiling") or {}
        profiling_config_obj = ProfilingConfig(**profiling_config)
        adapter.validate_profiling_config(profiling_config_obj)
        # validate output config
        output_config = self.config.get("output") or {}
        output_config_obj = OutputConfig(**output_config)
        # create run context
        context = RunContext(
            adapter=adapter,
            benchmark_key=benchmark_key,
            params=self.config.get("benchmark_params", {}),
            output_config=output_config_obj,
            profiling=profiling_config_obj,
        )
        # get benchmark instance and run
        benchmark = BenchmarkRegistry.get_benchmark_instance(benchmark_key, context)
        benchmark_result = benchmark.run()
        return benchmark_result

    def _resolve_benchmark_key(self) -> str:
        direct_key = self.config.get("benchmark")
        if direct_key:
            return direct_key

        origin = self.config.get("origin")
        source = self.config.get("source")
        name = self.config.get("name")
        if not (origin and source and name):
            raise ValueError(
                "Provide either 'benchmark' with 'origin/source/name' or 'origin', 'source', and 'name' fields."
            )
        return f"{origin}/{source}/{name}"