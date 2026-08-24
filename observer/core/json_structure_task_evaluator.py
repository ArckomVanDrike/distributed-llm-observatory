from __future__ import annotations

import json
from typing import Any

from observer.core.task_evaluator import TaskEvaluator
from observer.core.task_evidence import TaskCriterionEvidence
from observer.sut.base import SUTExecutionResult
from schemas.benchmark import BenchmarkTask
from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)


def _json_scalar_equal(
    observed: Any,
    expected: Any,
) -> bool:
    if isinstance(observed, bool) or isinstance(expected, bool):
        return (
            isinstance(observed, bool)
            and isinstance(expected, bool)
            and observed == expected
        )

    observed_is_number = isinstance(
        observed,
        (int, float),
    )
    expected_is_number = isinstance(
        expected,
        (int, float),
    )

    if observed_is_number or expected_is_number:
        return (
            observed_is_number
            and expected_is_number
            and observed == expected
        )

    return (
        type(observed) is type(expected)
        and observed == expected
    )


def _json_object_matches(
    observed: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    if observed.keys() != expected.keys():
        return False

    return all(
        _json_scalar_equal(
            observed[key],
            expected[key],
        )
        for key in expected
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
            and _json_object_matches(
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
