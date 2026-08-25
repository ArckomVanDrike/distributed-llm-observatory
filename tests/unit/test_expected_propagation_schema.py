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

_DEFAULT = object()


def make_task(
    *,
    expected_propagations,
    expected_actions=_DEFAULT,
    tool_results=_DEFAULT,
) -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-propagation-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Create an item, then inspect the created item.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="tool-result-propagated",
                description=(
                    "A tool result was propagated "
                    "to a later action."
                ),
            ),
        ],
        available_tools=[
            {
                "tool_name": "create_item",
                "description": "Create an item.",
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
            {
                "tool_name": "inspect_item",
                "description": "Inspect an item.",
                "parameters": {
                    "item_id": "string",
                },
            },
        ],
        tool_results=(
            [
                {
                    "tool_name": "create_item",
                    "result": {
                        "item_id": "item-742",
                    },
                },
            ]
            if tool_results is _DEFAULT
            else tool_results
        ),
        expected_actions=(
            [
                {
                    "tool_name": "create_item",
                    "arguments": {
                        "name": "delta",
                        "count": 4,
                    },
                },
                {
                    "tool_name": "inspect_item",
                    "arguments": {},
                },
            ]
            if expected_actions is _DEFAULT
            else expected_actions
        ),
        expected_propagations=expected_propagations,
    )


def propagation():
    return {
        "source_action_index": 0,
        "source_result_field": "item_id",
        "target_action_index": 1,
        "target_argument": "item_id",
    }


def test_task_accepts_expected_propagation():
    task = make_task(
        expected_propagations=[
            propagation(),
        ],
    )

    assert task.expected_propagations is not None
    assert len(task.expected_propagations) == 1

    expected = task.expected_propagations[0]

    assert expected.source_action_index == 0
    assert expected.source_result_field == "item_id"
    assert expected.target_action_index == 1
    assert expected.target_argument == "item_id"


def test_expected_propagation_round_trips():
    task = make_task(
        expected_propagations=[
            propagation(),
        ],
    )

    restored = BenchmarkTask.model_validate(
        task.model_dump()
    )

    assert (
        restored.expected_propagations
        == task.expected_propagations
    )


def test_expected_propagation_requires_expected_actions():
    with pytest.raises(
        ValidationError,
        match="expected_propagations",
    ):
        make_task(
            expected_propagations=[
                propagation(),
            ],
            expected_actions=None,
        )


def test_expected_propagation_requires_tool_results():
    with pytest.raises(
        ValidationError,
        match="expected_propagations",
    ):
        make_task(
            expected_propagations=[
                propagation(),
            ],
            tool_results=[],
        )


def test_expected_propagation_indices_must_exist():
    bad = propagation()
    bad["target_action_index"] = 2

    with pytest.raises(
        ValidationError,
        match="expected_propagations",
    ):
        make_task(
            expected_propagations=[
                bad,
            ],
        )


def test_expected_propagation_must_flow_forward():
    bad = propagation()
    bad["source_action_index"] = 1
    bad["target_action_index"] = 0

    with pytest.raises(
        ValidationError,
        match="expected_propagations",
    ):
        make_task(
            expected_propagations=[
                bad,
            ],
        )


def test_expected_propagation_source_field_must_exist():
    bad = propagation()
    bad["source_result_field"] = "missing_id"

    with pytest.raises(
        ValidationError,
        match="expected_propagations",
    ):
        make_task(
            expected_propagations=[
                bad,
            ],
        )


def test_expected_propagation_target_argument_must_exist():
    bad = propagation()
    bad["target_argument"] = "missing_argument"

    with pytest.raises(
        ValidationError,
        match="expected_propagations",
    ):
        make_task(
            expected_propagations=[
                bad,
            ],
        )


def test_propagated_argument_is_not_static_expected_argument():
    expected_actions = [
        {
            "tool_name": "create_item",
            "arguments": {
                "name": "delta",
                "count": 4,
            },
        },
        {
            "tool_name": "inspect_item",
            "arguments": {
                "item_id": "item-742",
            },
        },
    ]

    with pytest.raises(
        ValidationError,
        match="expected_propagations",
    ):
        make_task(
            expected_propagations=[
                propagation(),
            ],
            expected_actions=expected_actions,
        )
