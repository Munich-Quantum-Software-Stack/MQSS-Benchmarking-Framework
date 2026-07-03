from __future__ import annotations
from abc import ABC, abstractmethod
from mqssbench.framework.types import PipelineResult, RunContext, StorageConfig

class StorageError(Exception):
    pass

class StorageBackend(ABC):
    """Abstract storage backend."""

    def __init__(self, context: RunContext, config: StorageConfig):
        self.context = context
        self.config = config

    @abstractmethod
    def initialize(self) -> None:
        """Prepare storage (create paths, open DB, migrations)."""
        pass

    @abstractmethod
    def save_result(self, result: PipelineResult) -> str:
        """
        Persist the structured result (and return the path or URI to file, DB, etc.).
        Must be atomic: either succeed fully or raise StorageError.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Cleanup resources (close DB connections)."""
        pass
