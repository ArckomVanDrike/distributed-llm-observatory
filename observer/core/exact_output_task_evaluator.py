from __future__ import annotations

from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evidence import TaskCriterionEvidence
from observer.sut.base import SUTExecutionResult
from schemas.benchmark import BenchmarkTask
from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)


class ExactOutputTaskEvaluator(TaskEvaluator):
    """
    Evaluates a task by comparing the observed SUT output
    with the task's explicitly declared expected output.
    """

    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence: tuple[TaskCriterionEvidence, ...] | None = None,
    ) -> TaskEvaluation:
        expected = benchmark.expected_output_text

        if expected is None:
            raise ValueError(
                "Exact output evaluation requires "
                "expected_output_text."
            )

        passed = result.output_text == expected

        criteria = [
            TaskCriterionEvaluation(
                criterion=criterion.description,
                passed=passed,
                evidence=(
                    "Observed output exactly matches "
                    "the expected output."
                    if passed
                    else (
                        "Observed output does not exactly "
                        "match the expected output."
                    )
                ),
            )
            for criterion in benchmark.success_criteria
        ]

        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=criteria,
            passed=passed,
        )
