from typing import Type
from .storage_backend import StorageBackend
from ..framework.types import StorageConfig, RunContext

_STORAGE_REGISTRY: dict[str, Type[StorageBackend]] = {}

def register_storage(name: str):
    def _decor(cls):
        _STORAGE_REGISTRY[name] = cls
        return cls
    return _decor

def get_storage(name: str, context: RunContext, config: StorageConfig) -> StorageBackend:
    try:
        cls = _STORAGE_REGISTRY[name]
    except KeyError:
        raise ValueError(f"Unknown storage backend {name}")
    inst = cls(context=context, config=config)
    inst.initialize()
    return inst
