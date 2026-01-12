"""Library module containing concrete benchmark, adapter, and provider implementations."""

from .loader import auto_import_builtin_library

# Automatically register all builtin library modules
auto_import_builtin_library()

__all__ = []  