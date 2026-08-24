from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TaskCriterionEvidence:
    criterion_id: str
    passed: bool
    evidence: str | None = None


class TaskEvidenceCollector(ABC):
    """
    Observatory contract for collecting benchmark evidence
    after SUT execution.
    """

    @abstractmethod
    def collect(
        self,
    ) -> tuple[TaskCriterionEvidence, ...]:
        raise NotImplementedError
