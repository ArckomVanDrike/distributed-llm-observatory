import pytest
from pydantic import ValidationError

from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)
from schemas.target import TargetCapability


def make_task(
    *,
    expected_action,
    required_capabilities=None,
) -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-action-schema-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Call the provided tool exactly once.",
        required_capabilities=(
            required_capabilities
            if required_capabilities is not None
            else {
                TargetCapability.TEXT,
                TargetCapability.TOOLS,
            }
        ),
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="tool-called",
                description="The expected tool was called.",
            ),
        ],
        available_tools=[
            {
                "tool_name": "record_item",
                "description": "Record one item.",
                "parameters": {
                    "name": "string",
                    "count": "integer",
                    "active": "boolean",
                },
            },
        ],
        expected_action=expected_action,
    )


def test_benchmark_task_accepts_expected_action():
    task = make_task(
        expected_action={
            "tool_name": "record_item",
            "arguments": {
                "name": "delta",
                "count": 4,
                "active": True,
            },
            "call_count": 1,
        },
    )

    assert task.expected_action is not None
    assert task.expected_action.tool_name == "record_item"
    assert task.expected_action.arguments == {
        "name": "delta",
        "count": 4,
        "active": True,
    }
    assert task.expected_action.call_count == 1


def test_expected_action_round_trips_through_json():
    task = make_task(
        expected_action={
            "tool_name": "record_item",
            "arguments": {
                "name": "delta",
                "count": 4,
                "active": True,
            },
            "call_count": 1,
        },
    )

    restored = BenchmarkTask.model_validate_json(
        task.model_dump_json()
    )

    assert restored == task


def test_expected_action_rejects_nested_argument_object():
    with pytest.raises(ValidationError):
        make_task(
            expected_action={
                "tool_name": "record_item",
                "arguments": {
                    "item": {
                        "name": "delta",
                    },
                },
                "call_count": 1,
            },
        )


def test_expected_action_rejects_array_argument():
    with pytest.raises(ValidationError):
        make_task(
            expected_action={
                "tool_name": "record_item",
                "arguments": {
                    "names": [
                        "delta",
                        "alpha",
                    ],
                },
                "call_count": 1,
            },
        )


def test_expected_action_rejects_zero_call_count():
    with pytest.raises(ValidationError):
        make_task(
            expected_action={
                "tool_name": "record_item",
                "arguments": {
                    "name": "delta",
                },
                "call_count": 0,
            },
        )


def test_expected_action_requires_tools_capability():
    with pytest.raises(
        ValidationError,
        match="tools capability",
    ):
        make_task(
            expected_action={
                "tool_name": "record_item",
                "arguments": {
                    "name": "delta",
                },
                "call_count": 1,
            },
            required_capabilities={
                TargetCapability.TEXT,
            },
        )
