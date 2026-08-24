from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)
from schemas.target import TargetCapability


def test_benchmark_task_accepts_expected_json_object():
    task = BenchmarkTask(
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
        expected_output_json_object={
            "name": "delta",
            "count": 4,
            "active": True,
        },
    )

    assert task.expected_output_json_object == {
        "name": "delta",
        "count": 4,
        "active": True,
    }


def test_expected_json_object_round_trips():
    task = BenchmarkTask(
        schema_version="0.1",
        task_id="agent-protocol-structured-output-001",
        benchmark_version="0.1",
        evaluator_id="json-structure-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.INSTRUCTION_FOLLOWING,
        difficulty=BenchmarkDifficulty.EASY,
        task="Return the requested JSON object.",
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="json-structure-match",
                description="The JSON object matches.",
            ),
        ],
        expected_output_json_object={
            "name": "delta",
            "count": 4,
            "active": True,
            "note": None,
        },
    )

    restored = BenchmarkTask.model_validate_json(
        task.model_dump_json()
    )

    assert (
        restored.expected_output_json_object
        == task.expected_output_json_object
    )


def test_expected_json_object_rejects_nested_objects():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BenchmarkTask(
            schema_version="0.1",
            task_id="agent-protocol-structured-output-001",
            benchmark_version="0.1",
            evaluator_id="json-structure-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.INSTRUCTION_FOLLOWING,
            difficulty=BenchmarkDifficulty.EASY,
            task="Return the requested JSON object.",
            required_capabilities={
                TargetCapability.TEXT,
            },
            success_criteria=[
                BenchmarkSuccessCriterion(
                    criterion_id="json-structure-match",
                    description="The JSON object matches.",
                ),
            ],
            expected_output_json_object={
                "name": "delta",
                "metadata": {
                    "count": 4,
                },
            },
        )


def test_expected_json_object_rejects_array_values():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BenchmarkTask(
            schema_version="0.1",
            task_id="agent-protocol-structured-output-001",
            benchmark_version="0.1",
            evaluator_id="json-structure-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.INSTRUCTION_FOLLOWING,
            difficulty=BenchmarkDifficulty.EASY,
            task="Return the requested JSON object.",
            required_capabilities={
                TargetCapability.TEXT,
            },
            success_criteria=[
                BenchmarkSuccessCriterion(
                    criterion_id="json-structure-match",
                    description="The JSON object matches.",
                ),
            ],
            expected_output_json_object={
                "name": "delta",
                "items": [
                    "alpha",
                    "bravo",
                ],
            },
        )
