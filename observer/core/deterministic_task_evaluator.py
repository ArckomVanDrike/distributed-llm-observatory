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


class DeterministicTaskEvaluator(TaskEvaluator):
    """
    Evaluates benchmark criteria from explicit structured SUT evidence.
    """

    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence: tuple[TaskCriterionEvidence, ...] | None = None,
    ) -> TaskEvaluation:
        if evidence is None:
            raise ValueError(
                "Deterministic evaluation requires "
                "external criterion evidence."
            )

        evidence_by_id = {}

        for evidence_item in evidence:
            if evidence_item.criterion_id in evidence_by_id:
                raise ValueError(
                    "Duplicate criterion evidence for "
                    f"{evidence_item.criterion_id!r}."
                )

            evidence_by_id[evidence_item.criterion_id] = evidence_item

        criteria = []

        for criterion in benchmark.success_criteria:
            try:
                evidence = evidence_by_id[criterion.criterion_id]
            except KeyError:
                raise ValueError(
                    "Missing criterion evidence for "
                    f"{criterion.criterion_id!r}."
                ) from None

            criteria.append(
                TaskCriterionEvaluation(
                    criterion=criterion.description,
                    passed=evidence.passed,
                    evidence=evidence.evidence,
                )
            )

        return TaskEvaluation(
            task_id=benchmark.task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=criteria,
            passed=all(
                criterion.passed
                for criterion in criteria
            ),
        )
