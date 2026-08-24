import pytest
from pydantic import ValidationError

from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)


def build_task(
    *,
    expected_output_text: str,
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
            "text",
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


def test_benchmark_task_stores_expected_output_text():
    task = build_task(
        expected_output_text="DLLO-AGENT-SMOKE-001",
    )

    assert (
        task.expected_output_text
        == "DLLO-AGENT-SMOKE-001"
    )


def test_benchmark_task_rejects_empty_expected_output_text():
    with pytest.raises(ValidationError):
        build_task(
            expected_output_text="",
        )
