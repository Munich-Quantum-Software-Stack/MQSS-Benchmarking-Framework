from __future__ import annotations
from colorama import Fore, Style, init as colorama_init
from typing import Iterable, List, Optional
from mqssbench.framework.types import PipelineResult, CircuitExecutionResult, PipelineEngineExecutionResult

# needed for Windows
colorama_init(autoreset=True)


def _format_execution_entry(entry, idx: int) -> list[str]:
    """Format either a standard ExecutionResult or a generic pipeline record."""
    lines = [f"  {Fore.GREEN}Execution {idx + 1}:{Style.RESET_ALL}"]

    if isinstance(entry, CircuitExecutionResult):
        lines.append(f"    Job ID: {entry.job_id}")
        lines.append("    Counts:")
        for state, count in entry.counts.items():
            lines.append(f"      {state}: {count}")

        if entry.profiling_metrics and entry.profiling_metrics.params:
            lines.append("    Profiling:")
            for pkey, pval in entry.profiling_metrics.params.items():
                lines.append(f"      {pkey}: {pval}")
        return lines

    if isinstance(entry, PipelineEngineExecutionResult):
        lines.append(f"    Pipeline: {entry.pipeline}")
        lines.append(f"    Pipeline Status: {entry.pipeline_status}")
        payload = entry.payload
        if isinstance(payload, dict):
            if "result" in payload:
                lines.append(f"    Result: {payload['result']}")
            if "runtime" in payload:
                lines.append(f"    Runtime: {payload['runtime']}")
        return lines

    lines.append(f"    Payload: {entry}")
    return lines


def format_benchmark_result(result: PipelineResult) -> str:
    """Return a clean, colored, human readable string for PipelineResult."""
    parts = []

    # header
    parts.append(f"{Fore.CYAN}{Style.BRIGHT}Run ID: {Style.RESET_ALL}{result.run_id}")
    parts.append(f"{Fore.CYAN}{Style.BRIGHT}Benchmark: {Style.RESET_ALL}{result.benchmark_key}")
    parts.append(f"{Fore.CYAN}{Style.BRIGHT}Category: {Style.RESET_ALL}{result.category}")
    parts.append(f"{Fore.CYAN}{Style.BRIGHT}Status: {Style.RESET_ALL}{result.status}")

    # parameters
    if result.params:
        parts.append(f"{Fore.YELLOW}Parameters:{Style.RESET_ALL}")
        for key, value in result.params.items():
            parts.append(f"  {Fore.WHITE}{key}{Style.RESET_ALL}: {value}")

    # execution results
    if result.execution_results:
        parts.append(f"{Fore.GREEN}Execution Results:{Style.RESET_ALL}")
        exec_results: Iterable = result.execution_results.values() \
            if isinstance(result.execution_results, dict) else result.execution_results

        for idx, ex in enumerate(exec_results):
            parts.extend(_format_execution_entry(ex, idx))

    # analysis
    if result.analysis_result:
        parts.append(f"{Fore.MAGENTA}Analysis:{Style.RESET_ALL}")

        # metrics
        if result.analysis_result.metrics:
            parts.append(f"  {Fore.MAGENTA}Metrics:")
            for key, value in result.analysis_result.metrics.items():
                parts.append(f"    {Fore.WHITE}{key}{Style.RESET_ALL}: {value}")

        # artifacts
        if result.analysis_result.artifacts:
            parts.append(f"  {Fore.MAGENTA}Artifacts:")
            for name, path in result.analysis_result.artifacts.items():
                parts.append(f"    {Fore.WHITE}{name}{Style.RESET_ALL}: {path}")

    parts.append("")  # blank line for separation

    if result.storage_location:
        parts.append(f"{Fore.CYAN}{Style.BRIGHT}Stored at:{Style.RESET_ALL} {result.storage_location}")

    return "\n".join(parts)


def format_registry_lists(
    benchmarks: Optional[List[str]] = None,
    providers: Optional[List[str]] = None,
    adapters: Optional[List[str]] = None,
) -> str:
    """Return a nicely formatted string for CLI display. Skips empty sections."""
    lines = []

    if benchmarks:
        lines.append(f"{Fore.CYAN}Available benchmarks:{Style.RESET_ALL}")
        lines.extend([f"  - {b}" for b in benchmarks])

    if providers:
        if lines:  # add spacing if previous section exists
            lines.append("")
        lines.append(f"{Fore.YELLOW}Available circuit providers:{Style.RESET_ALL}")
        lines.extend([f"  - {p}" for p in providers])

    if adapters:
        if lines:
            lines.append("")
        lines.append(f"{Fore.MAGENTA}Available adapters:{Style.RESET_ALL}")
        lines.extend([f"  - {a}" for a in adapters])

    return "\n" + "\n".join(lines)
