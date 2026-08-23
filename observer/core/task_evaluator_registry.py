from __future__ import annotations

from observer.core.task_evaluator import TaskEvaluator
from schemas.benchmark import BenchmarkTask


class TaskEvaluatorRegistry:
    """
    Explicit registry of task evaluators keyed by stable evaluator ID.
    """

    def __init__(self) -> None:
        self._evaluators: dict[str, TaskEvaluator] = {}

    def register(
        self,
        evaluator_id: str,
        evaluator: TaskEvaluator,
    ) -> None:
        if evaluator_id in self._evaluators:
            raise ValueError(
                f"Evaluator {evaluator_id!r} is already registered."
            )

        self._evaluators[evaluator_id] = evaluator

    def resolve(
        self,
        benchmark: BenchmarkTask,
    ) -> TaskEvaluator:
        try:
            return self._evaluators[benchmark.evaluator_id]
        except KeyError:
            raise KeyError(
                "No task evaluator registered for "
                f"{benchmark.evaluator_id!r}."
            ) from None
