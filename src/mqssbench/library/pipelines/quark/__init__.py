"""QUARK pipeline plugin (optional dependency)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register() -> None:
    """Register the QUARK benchmark pipeline when quark is installed."""
    try:
        from .workflow import QUARKBenchmarkPipeline
    except ImportError:
        logger.debug("quark not installed; skipping QUARK pipeline registration")
        return

    from mqssbench.framework.benchmark_registry import BenchmarkRegistry

    BenchmarkRegistry.register_benchmark(QUARKBenchmarkPipeline)
