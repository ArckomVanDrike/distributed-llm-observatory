from datetime import datetime, timezone

import pytest

from observer.core.json_structure_task_evaluator import (
    JsonStructureTaskEvaluator,
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

EXPECTED_OBJECT = {
    "name": "delta",
    "count": 4,
    "active": True,
}


def build_task(
    *,
    expected_output_json_object=EXPECTED_OBJECT,
) -> BenchmarkTask:
    return BenchmarkTask(
        schema_version="0.1",
        task_id="agent-protocol-structured-output-001",
        benchmark_version="0.1",
        evaluator_id="json-structure-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.INSTRUCTION_FOLLOWING,
        difficulty=BenchmarkDifficulty.EASY,
        task=(
            "Return only a JSON object with name delta, "
            "count 4, and active true."
        ),
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="json-structure-match",
                description=(
                    "The observed output is exactly one JSON "
                    "object with the expected keys and values."
                ),
            ),
        ],
        expected_output_json_object=(
            expected_output_json_object
        ),
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
            task_id="agent-protocol-structured-output-001",
            target_id="example-agent",
        ),
        started_at_utc=now,
        finished_at_utc=now,
        latency_ms=1.0,
        task_completed=task_completed,
        output_text=output_text,
    )


def test_json_structure_passes_equivalent_object():
    evaluation = JsonStructureTaskEvaluator().evaluate(
        build_task(),
        build_result(
            output_text=(
                '{\n'
                '  "active": true,\n'
                '  "count": 4,\n'
                '  "name": "delta"\n'
                '}'
            ),
            task_completed=False,
        ),
    )

    assert (
        evaluation.method
        is TaskEvaluationMethod.DETERMINISTIC
    )
    assert evaluation.passed is True
    assert evaluation.criteria[0].passed is True


@pytest.mark.parametrize(
    "output_text",
    [
        None,
        "not json",
        '["delta", 4, true]',
        '{"name":"delta","count":4}',
        (
            '{"name":"delta","count":4,'
            '"active":true,"extra":"value"}'
        ),
        '{"name":"wrong","count":4,"active":true}',
        (
            "```json\n"
            '{"name":"delta","count":4,"active":true}\n'
            "```"
        ),
    ],
)
def test_json_structure_fails_non_matching_output(
    output_text,
):
    evaluation = JsonStructureTaskEvaluator().evaluate(
        build_task(),
        build_result(
            output_text=output_text,
            task_completed=True,
        ),
    )

    assert evaluation.passed is False
    assert evaluation.criteria[0].passed is False


def test_json_structure_distinguishes_boolean_from_number():
    evaluation = JsonStructureTaskEvaluator().evaluate(
        build_task(),
        build_result(
            output_text=(
                '{"name":"delta","count":4,"active":1}'
            ),
            task_completed=True,
        ),
    )

    assert evaluation.passed is False


def test_json_structure_requires_expected_object():
    with pytest.raises(
        ValueError,
        match="expected_output_json_object",
    ):
        JsonStructureTaskEvaluator().evaluate(
            build_task(
                expected_output_json_object=None,
            ),
            build_result(
                output_text=(
                    '{"name":"delta","count":4,'
                    '"active":true}'
                ),
                task_completed=True,
            ),
        )
