from __future__ import annotations

from abc import ABC, abstractmethod

from schemas.record import ObservationRecord


class ObservationStore(ABC):
    """Base interface for local Observatory persistence backends."""

    @abstractmethod
    def append(self, record: ObservationRecord) -> None:
        """Persist one observation record."""
        raise NotImplementedError

    @abstractmethod
    def load_all(self) -> list[ObservationRecord]:
        """Load all persisted observation records."""
        raise NotImplementedError
