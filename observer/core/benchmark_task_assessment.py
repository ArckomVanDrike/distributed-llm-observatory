from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observer.core.benchmark_task_runner import (
    BenchmarkTaskRun,
    BenchmarkTaskRunner,
)
from observer.core.task_evaluator import TaskEvaluator
from schemas.benchmark import BenchmarkTask
from schemas.evaluation import TaskEvaluation


@dataclass(frozen=True)
class AssessedBenchmarkTaskRun:
    run: BenchmarkTaskRun
    evaluation: TaskEvaluation


class BenchmarkTaskAssessmentRunner:
    """
    Executes a benchmark task and evaluates the resulting SUT observation.
    """

    def __init__(
        self,
        *,
        task_runner: BenchmarkTaskRunner,
        evaluator: TaskEvaluator,
    ) -> None:
        self.task_runner = task_runner
        self.evaluator = evaluator

    def run(
        self,
        benchmark: BenchmarkTask,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AssessedBenchmarkTaskRun:
        run = self.task_runner.run(
            benchmark,
            metadata=metadata,
        )

        evaluation = self.evaluator.evaluate(
            benchmark,
            run.observation.result,
        )

        if evaluation.task_id != benchmark.task_id:
            raise ValueError(
                "Task evaluation task_id does not match "
                f"the benchmark task_id: "
                f"evaluation={evaluation.task_id!r}, "
                f"benchmark={benchmark.task_id!r}."
            )

        return AssessedBenchmarkTaskRun(
            run=run,
            evaluation=evaluation,
        )
