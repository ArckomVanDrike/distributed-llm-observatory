from __future__ import annotations

import json
from typing import Any

from observer.core.json_value_comparison import (
    json_flat_object_equal,
)
from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evidence import TaskCriterionEvidence
from observer.sut.base import SUTExecutionResult
from schemas.benchmark import BenchmarkTask
from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)


class JsonStructureTaskEvaluator(TaskEvaluator):
    """
    Evaluates whether the observed output is exactly one JSON
    object with the expected flat keys and scalar values.
    """

    def evaluate(
        self,
        benchmark: BenchmarkTask,
        result: SUTExecutionResult,
        *,
        evidence: tuple[TaskCriterionEvidence, ...] | None = None,
    ) -> TaskEvaluation:
        expected = benchmark.expected_output_json_object

        if expected is None:
            raise ValueError(
                "JSON structure evaluation requires "
                "expected_output_json_object."
            )

        observed: Any = None

        if result.output_text is not None:
            try:
                observed = json.loads(
                    result.output_text
                )
            except (
                json.JSONDecodeError,
                TypeError,
            ):
                observed = None

        passed = (
            isinstance(observed, dict)
            and json_flat_object_equal(
                observed,
                expected,
            )
        )

        criteria = [
            TaskCriterionEvaluation(
                criterion=criterion.description,
                passed=passed,
                evidence=(
                    "Observed output is a JSON object with "
                    "the expected keys and values."
                    if passed
                    else (
                        "Observed output is not a JSON object "
                        "with exactly the expected keys and "
                        "values."
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
