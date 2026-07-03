"""Library module containing concrete benchmark, adapter, and provider implementations."""

from .loader import load_plugins

# Automatically register all builtin library modules
load_plugins()

__all__ = []  