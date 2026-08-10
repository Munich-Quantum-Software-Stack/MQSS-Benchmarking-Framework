"""Run smoke benchmarks, especially for making sure the device adapter works as expected."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from types import ModuleType

from mqssbench.cli.formatting import format_benchmark_result
from mqssbench.runtime.benchmark_manager import BenchmarkManager

SMOKE_DIR = Path(__file__).resolve().parent
SKIP_MODULES = frozenset({"run"})


def discover_smoke_modules() -> list[str]:
    return sorted(
        path.stem
        for path in SMOKE_DIR.glob("*.py")
        if path.stem not in SKIP_MODULES and not path.stem.startswith("_")
    )


def load_smoke_modules(selected: list[str] | None = None) -> list[ModuleType]:
    if str(SMOKE_DIR) not in sys.path:
        sys.path.insert(0, str(SMOKE_DIR))

    available = discover_smoke_modules()
    if selected:
        unknown = sorted(set(selected) - set(available))
        if unknown:
            raise SystemExit(
                f"Unknown smoke test(s): {', '.join(unknown)}. "
                f"Available: {', '.join(available)}"
            )
        module_names = selected
    else:
        module_names = available

    return [importlib.import_module(name) for name in module_names]


def collect_smoke_configs(modules: list[ModuleType]) -> list[dict]:
    configs: list[dict] = []
    for module in modules:
        config = getattr(module, "SMOKE_CONFIG", None)
        if config is None:
            continue
        if not isinstance(config, dict):
            raise TypeError(f"{module.__name__}.SMOKE_CONFIG must be a dict")
        configs.append(config)
    return configs


def main() -> None:
    available = discover_smoke_modules()
    parser = argparse.ArgumentParser(description="Run mqssbench smoke checks")
    parser.add_argument(
        "tests",
        nargs="*",
        metavar="TEST",
        help=(
            "Smoke module(s) to run, e.g. mqss_pennylane_bell mqss_qiskit_bell. "
            f"Default: all ({', '.join(available) or 'none found'})"
        ),
    )
    args = parser.parse_args()

    selected = args.tests or None
    modules = load_smoke_modules(selected)
    configs = collect_smoke_configs(modules)

    if not configs:
        raise SystemExit("No smoke configs found. Each smoke module needs SMOKE_CONFIG.")

    results = []
    for config in configs:
        results.extend(BenchmarkManager(config).dispatch())

    for result in results:
        print(format_benchmark_result(result))
        print()


if __name__ == "__main__":
    main()
