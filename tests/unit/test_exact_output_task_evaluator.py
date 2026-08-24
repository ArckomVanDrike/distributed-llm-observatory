from datetime import datetime, timezone

import pytest

from observer.core.exact_output_task_evaluator import (
    ExactOutputTaskEvaluator,
)
from observer.sut.base import (
    SUTExecutionContext,
    SUTExecutionResult,
)
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)
from schemas.evaluation import TaskEvaluationMethod
from schemas.target import TargetCapability

EXPECTED_OUTPUT = "DLLO-AGENT-SMOKE-001"


def build_task(
    *,
    expected_output_text: str | None = EXPECTED_OUTPUT,
) -> BenchmarkTask:
    return BenchmarkTask(
        schema_version="0.1",
        task_id="agent-protocol-smoke-001",
        benchmark_version="0.1",
        evaluator_id="exact-output-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task=(
            "Return exactly DLLO-AGENT-SMOKE-001 "
            "and no additional characters."
        ),
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="output-exact-match",
                description=(
                    "The observed output contains exactly "
                    "DLLO-AGENT-SMOKE-001."
                ),
            ),
        ],
        expected_output_text=expected_output_text,
    )


def build_result(
    *,
    output_text: str | None,
    task_completed: bool,
) -> SUTExecutionResult:
    now = datetime.now(timezone.utc)

    return SUTExecutionResult(
        context=SUTExecutionContext(
            observer_id="observer-test",
            region_code="CL-Los-Lagos",
            benchmark_version="0.1",
            task_id="agent-protocol-smoke-001",
            target_id="example-agent",
        ),
        started_at_utc=now,
        finished_at_utc=now,
        latency_ms=1.0,
        task_completed=task_completed,
        output_text=output_text,
    )


def test_exact_output_passes_even_when_sut_reports_not_completed():
    evaluation = ExactOutputTaskEvaluator().evaluate(
        build_task(),
        build_result(
            output_text=EXPECTED_OUTPUT,
            task_completed=False,
        ),
    )

    assert evaluation.method is TaskEvaluationMethod.DETERMINISTIC
    assert evaluation.passed is True
    assert evaluation.criteria[0].passed is True


def test_exact_output_fails_even_when_sut_reports_completed():
    evaluation = ExactOutputTaskEvaluator().evaluate(
        build_task(),
        build_result(
            output_text="wrong output",
            task_completed=True,
        ),
    )

    assert evaluation.passed is False
    assert evaluation.criteria[0].passed is False


def test_exact_output_fails_when_output_is_missing():
    evaluation = ExactOutputTaskEvaluator().evaluate(
        build_task(),
        build_result(
            output_text=None,
            task_completed=True,
        ),
    )

    assert evaluation.passed is False
    assert evaluation.criteria[0].passed is False


def test_exact_output_requires_expected_output_text():
    with pytest.raises(
        ValueError,
        match="expected_output_text",
    ):
        ExactOutputTaskEvaluator().evaluate(
            build_task(
                expected_output_text=None,
            ),
            build_result(
                output_text=EXPECTED_OUTPUT,
                task_completed=True,
            ),
        )
