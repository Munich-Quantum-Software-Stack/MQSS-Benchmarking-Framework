from __future__ import annotations
from colorama import Fore, Style, init as colorama_init
from typing import Iterable, List, Optional
from mqssbench.framework.types import BenchmarkResult, ExecutionResult

# needed for Windows
colorama_init(autoreset=True)

def format_benchmark_result(result: BenchmarkResult) -> str:
    """Return a clean, colored, human readable string for BenchmarkResult."""
    parts = []

    # header
    parts.append(f"{Fore.CYAN}{Style.BRIGHT}Benchmark: {Style.RESET_ALL}{result.benchmark_key}")

    # parameters
    if result.params:
        parts.append(f"{Fore.YELLOW}Parameters:{Style.RESET_ALL}")
        for key, value in result.params.items():
            parts.append(f"  {Fore.WHITE}{key}{Style.RESET_ALL}: {value}")

    # execution results
    if result.execution_results:
        parts.append(f"{Fore.GREEN}Execution Results:{Style.RESET_ALL}")
        exec_results: Iterable[ExecutionResult] = result.execution_results.values() \
            if isinstance(result.execution_results, dict) else result.execution_results

        for idx, ex in enumerate(exec_results):
            parts.append(f"  {Fore.GREEN}Execution {idx + 1}:{Style.RESET_ALL}")
            parts.append("    Counts:")
            for state, count in ex.counts.items():
                parts.append(f"      {state}: {count}")

            if ex.profiling_metrics and ex.profiling_metrics.params:
                parts.append("    Profiling:")
                for pkey, pval in ex.profiling_metrics.params.items():
                    parts.append(f"      {pkey}: {pval}")

    # analysis
    if result.analysis_result and result.analysis_result.results:
        parts.append(f"{Fore.MAGENTA}Analysis:{Style.RESET_ALL}")
        for key, value in result.analysis_result.results.items():
            parts.append(f"  {Fore.WHITE}{key}{Style.RESET_ALL}: {value}")

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
