from typing import Any, Dict
import uuid
import os
from datetime import datetime
from ..framework import AdapterRegistry
from ..framework import RunContext, BenchmarkRegistry
from ..framework.types import ProfilingConfig, BenchmarkResult, ReportConfig, StorageConfig
from ..framework.utils import show_artifacts
from ..storage import save_result_json
from dacite import from_dict, Config
import dataclasses

class BenchmarkRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self) -> BenchmarkResult:
        # determine run directory
        output_dir = self.config.get("output_dir")
        if not output_dir:
            raise ValueError("output_dir must be specified in the configuration.")
        run_id = uuid.uuid4().hex
        run_tag = f"{datetime.utcnow():%Y%m%dT%H%M%SZ}_{run_id[:8]}"
        run_dir = os.path.join(output_dir, run_tag)

        # get and validate adapter
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

        # report config
        report_config = self.config.get("report") or {}
        report_config_obj = from_dict(data_class=ReportConfig, data=report_config, config=Config(strict=True))

        # create run context
        context = RunContext(
            run_id=run_id,
            run_dir=run_dir,
            adapter=adapter,
            benchmark_key=benchmark_key,
            params=self.config.get("benchmark_params", {}),
            report_config=report_config_obj,
            profiling=profiling_config_obj,
        )
        # get benchmark instance and run
        benchmark = BenchmarkRegistry.get_benchmark_instance(benchmark_key, context)
        benchmark_result = benchmark.run()

        # TODO: this is temporarily here until we have a proper storage component
        # storage config
        storage_config = self.config.get("storage") or {}
        if storage_config:
            storage_config_obj = from_dict(data_class=StorageConfig, data=storage_config, config=Config(strict=True))

            # save result if configured
            if storage_config_obj.type == "file" and getattr(storage_config_obj.file, "format", None) == "json":
                saved = save_result_json(context, benchmark_result)
                if saved:
                    benchmark_result = dataclasses.replace(
                        benchmark_result,
                        storage_location=saved
                    )

        # show plots if configured
        if report_config_obj.analysis.visualization.enabled and report_config_obj.analysis.visualization.show:
            show_artifacts(benchmark_result.analysis_result.artifacts.values())
            
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