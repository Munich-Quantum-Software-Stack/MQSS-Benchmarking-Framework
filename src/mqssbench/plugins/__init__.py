"""Plugin loading for built-in and third-party MQSSBench plugins."""

from .manager import (
    load_plugins,
)

__all__ = [
    "load_plugins",
]