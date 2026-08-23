import pytest
from pydantic import ValidationError

from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)


def test_valid_deterministic_task_evaluation():
    evaluation = TaskEvaluation(
        task_id="agent-coding-001",
        method=TaskEvaluationMethod.DETERMINISTIC,
        criteria=[
            TaskCriterionEvaluation(
                criterion="All tests pass.",
                passed=True,
                evidence="pytest: 42 passed",
            ),
            TaskCriterionEvaluation(
                criterion="No unrelated files are modified.",
                passed=True,
                evidence="git diff contains only expected files",
            ),
        ],
        passed=True,
    )

    assert evaluation.schema_version == "0.1"
    assert evaluation.passed is True
    assert len(evaluation.criteria) == 2


def test_valid_human_task_evaluation():
    evaluation = TaskEvaluation(
        task_id="memory-recall-001",
        method=TaskEvaluationMethod.HUMAN,
        criteria=[
            TaskCriterionEvaluation(
                criterion="The stored fact is recalled correctly.",
                passed=True,
                evidence="Human reviewer confirmed exact recall.",
            ),
        ],
        passed=True,
    )

    assert evaluation.method is TaskEvaluationMethod.HUMAN


def test_task_evaluation_requires_at_least_one_criterion():
    with pytest.raises(ValidationError):
        TaskEvaluation(
            task_id="agent-coding-001",
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[],
            passed=True,
        )


def test_task_evaluation_rejects_overall_pass_when_criterion_failed():
    with pytest.raises(
        ValidationError,
        match="overall",
    ):
        TaskEvaluation(
            task_id="agent-coding-001",
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion="All tests pass.",
                    passed=False,
                    evidence="1 test failed",
                ),
            ],
            passed=True,
        )


def test_task_evaluation_rejects_overall_failure_when_all_criteria_pass():
    with pytest.raises(
        ValidationError,
        match="overall",
    ):
        TaskEvaluation(
            task_id="agent-coding-001",
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion="All tests pass.",
                    passed=True,
                    evidence="42 passed",
                ),
            ],
            passed=False,
        )


def test_task_criterion_requires_nonempty_text():
    with pytest.raises(ValidationError):
        TaskCriterionEvaluation(
            criterion=" ",
            passed=True,
        )


def test_task_id_uses_stable_slug_format():
    with pytest.raises(ValidationError):
        TaskEvaluation(
            task_id="Bad Task ID",
            method=TaskEvaluationMethod.HUMAN,
            criteria=[
                TaskCriterionEvaluation(
                    criterion="Task succeeds.",
                    passed=True,
                ),
            ],
            passed=True,
        )
