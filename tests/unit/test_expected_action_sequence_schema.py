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


def make_task(**overrides):
    values = {
        "task_id": "agent-action-sequence-001",
        "benchmark_version": "0.1",
        "evaluator_id": "deterministic-evidence-v0-1",
        "family": BenchmarkFamily.AGENT,
        "category": BenchmarkCategory.TECHNICAL,
        "difficulty": BenchmarkDifficulty.EASY,
        "task": "Persist delta and then inspect it.",
        "required_capabilities": {
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
        "success_criteria": [
            BenchmarkSuccessCriterion(
                criterion_id="tool-sequence-observed",
                description=(
                    "The expected action sequence was observed."
                ),
            ),
        ],
        "available_tools": [
            {
                "tool_name": "record_item",
                "description": "Persist an item.",
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
            {
                "tool_name": "inspect_item",
                "description": "Inspect an item.",
                "parameters": {
                    "name": "string",
                },
            },
        ],
    }

    values.update(overrides)

    return BenchmarkTask(**values)


def expected_sequence():
    return [
        {
            "tool_name": "record_item",
            "arguments": {
                "name": "delta",
                "count": 4,
            },
        },
        {
            "tool_name": "inspect_item",
            "arguments": {
                "name": "delta",
            },
        },
    ]


def test_task_accepts_expected_action_sequence():
    task = make_task(
        expected_actions=expected_sequence(),
    )

    assert task.expected_action is None
    assert task.expected_actions is not None

    assert [
        action.tool_name
        for action in task.expected_actions
    ] == [
        "record_item",
        "inspect_item",
    ]


def test_expected_action_sequence_preserves_order():
    task = make_task(
        expected_actions=expected_sequence(),
    )

    dumped = task.model_dump()
    restored = BenchmarkTask.model_validate(dumped)

    assert restored.expected_actions is not None

    assert [
        action.tool_name
        for action in restored.expected_actions
    ] == [
        "record_item",
        "inspect_item",
    ]


def test_expected_action_sequence_rejects_empty_sequence():
    with pytest.raises(ValidationError):
        make_task(
            expected_actions=[],
        )


def test_expected_action_sequence_requires_tools_capability():
    with pytest.raises(ValidationError):
        make_task(
            required_capabilities={
                TargetCapability.TEXT,
            },
            available_tools=[],
            expected_actions=expected_sequence(),
        )


def test_expected_action_sequence_requires_available_tools():
    with pytest.raises(ValidationError):
        make_task(
            available_tools=[],
            expected_actions=expected_sequence(),
        )


def test_expected_action_sequence_tool_must_be_available():
    sequence = expected_sequence()

    sequence[1] = {
        "tool_name": "delete_item",
        "arguments": {
            "name": "delta",
        },
    }

    with pytest.raises(ValidationError):
        make_task(
            expected_actions=sequence,
        )


def test_task_rejects_single_and_sequence_expectations_together():
    with pytest.raises(ValidationError):
        make_task(
            expected_action={
                "tool_name": "record_item",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
            expected_actions=expected_sequence(),
        )
