from __future__ import annotations

from abc import ABC, abstractmethod

from observer.core.task_evidence import TaskCriterionEvidence
from observer.sut.base import SUTExecutionResult
from schemas.benchmark import BenchmarkTask
from schemas.evaluation import TaskEvaluation


class TaskEvaluator(ABC):
    """
    Observatory contract for evaluating a completed benchmark task.
    """

    @abstractmethod
    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence: tuple[TaskCriterionEvidence, ...] | None = None,
    ) -> TaskEvaluation:
        raise NotImplementedError
