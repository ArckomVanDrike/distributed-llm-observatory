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
    expected_branches=_DEFAULT,
    expected_actions=_DEFAULT,
    tool_results=_DEFAULT,
):
    if expected_actions is _DEFAULT:
        expected_actions = [
            {
                "tool_name": "check_item",
                "arguments": {
                    "name": "delta",
                },
            },
        ]

    if tool_results is _DEFAULT:
        tool_results = [
            {
                "tool_name": "check_item",
                "result": {
                    "state": "missing",
                },
            },
        ]

    if expected_branches is _DEFAULT:
        expected_branches = {
            "source_action_index": 0,
            "source_result_field": "state",
            "options": [
                {
                    "expected_value": "missing",
                    "action": {
                        "tool_name": "create_item",
                        "arguments": {
                            "name": "delta",
                            "count": 4,
                        },
                    },
                },
                {
                    "expected_value": "present",
                    "action": {
                        "tool_name": "inspect_item",
                        "arguments": {
                            "name": "delta",
                        },
                    },
                },
            ],
        }

    return BenchmarkTask(
        task_id="agent-multi-branch-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task=(
            "Check the item state and take the "
            "appropriate next action."
        ),
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="branch-selected",
                description=(
                    "The runtime-dependent branch "
                    "was selected."
                ),
            ),
        ],
        available_tools=[
            {
                "tool_name": "check_item",
                "description": (
                    "Return the current state of an item."
                ),
                "parameters": {
                    "name": "string",
                },
            },
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
                    "name": "string",
                },
            },
        ],
        tool_results=tool_results,
        expected_actions=expected_actions,
        expected_branches=expected_branches,
    )


def test_task_accepts_expected_branches():
    task = make_task()

    assert task.expected_branches is not None
    assert task.expected_branches.source_action_index == 0
    assert (
        task.expected_branches.source_result_field
        == "state"
    )

    assert len(task.expected_branches.options) == 2

    missing, present = task.expected_branches.options

    assert missing.expected_value == "missing"
    assert missing.action.tool_name == "create_item"
    assert missing.action.arguments == {
        "name": "delta",
        "count": 4,
    }

    assert present.expected_value == "present"
    assert present.action.tool_name == "inspect_item"
    assert present.action.arguments == {
        "name": "delta",
    }


def test_expected_branches_round_trip():
    task = make_task()

    restored = BenchmarkTask.model_validate(
        task.model_dump()
    )

    assert (
        restored.expected_branches
        == task.expected_branches
    )


def test_expected_branches_require_expected_actions():
    with pytest.raises(
        ValidationError,
        match="expected_branches",
    ):
        make_task(
            expected_actions=None,
        )


def test_expected_branches_require_tool_results():
    with pytest.raises(
        ValidationError,
        match="expected_branches",
    ):
        make_task(
            tool_results=[],
        )


def test_expected_branches_source_index_must_exist():
    branches = {
        "source_action_index": 1,
        "source_result_field": "state",
        "options": [
            {
                "expected_value": "missing",
                "action": {
                    "tool_name": "create_item",
                    "arguments": {
                        "name": "delta",
                        "count": 4,
                    },
                },
            },
        ],
    }

    with pytest.raises(
        ValidationError,
        match="expected_branches",
    ):
        make_task(
            expected_branches=branches,
        )


def test_expected_branches_source_field_must_exist():
    branches = {
        "source_action_index": 0,
        "source_result_field": "unknown",
        "options": [
            {
                "expected_value": "missing",
                "action": {
                    "tool_name": "create_item",
                    "arguments": {
                        "name": "delta",
                        "count": 4,
                    },
                },
            },
        ],
    }

    with pytest.raises(
        ValidationError,
        match="expected_branches",
    ):
        make_task(
            expected_branches=branches,
        )


def test_expected_branch_option_values_must_be_unique():
    branches = {
        "source_action_index": 0,
        "source_result_field": "state",
        "options": [
            {
                "expected_value": "missing",
                "action": {
                    "tool_name": "create_item",
                    "arguments": {},
                },
            },
            {
                "expected_value": "missing",
                "action": {
                    "tool_name": "inspect_item",
                    "arguments": {},
                },
            },
        ],
    }

    with pytest.raises(
        ValidationError,
        match="expected_branches",
    ):
        make_task(
            expected_branches=branches,
        )


def test_expected_branch_option_tool_must_be_available():
    branches = {
        "source_action_index": 0,
        "source_result_field": "state",
        "options": [
            {
                "expected_value": "missing",
                "action": {
                    "tool_name": "unknown_tool",
                    "arguments": {},
                },
            },
        ],
    }

    with pytest.raises(
        ValidationError,
        match="expected_branches",
    ):
        make_task(
            expected_branches=branches,
        )


def test_configured_runtime_value_requires_matching_option():
    branches = {
        "source_action_index": 0,
        "source_result_field": "state",
        "options": [
            {
                "expected_value": "present",
                "action": {
                    "tool_name": "inspect_item",
                    "arguments": {
                        "name": "delta",
                    },
                },
            },
        ],
    }

    with pytest.raises(
        ValidationError,
        match="expected_branches",
    ):
        make_task(
            expected_branches=branches,
        )


def test_expected_branches_use_json_numeric_semantics():
    branches = {
        "source_action_index": 0,
        "source_result_field": "state",
        "options": [
            {
                "expected_value": 1,
                "action": {
                    "tool_name": "create_item",
                    "arguments": {
                        "name": "delta",
                        "count": 4,
                    },
                },
            },
        ],
    }

    task = make_task(
        tool_results=[
            {
                "tool_name": "check_item",
                "result": {
                    "state": 1.0,
                },
            },
        ],
        expected_branches=branches,
    )

    assert task.expected_branches is not None
    assert (
        task.expected_branches.options[0].expected_value
        == 1
    )


def test_expected_branch_option_numeric_values_must_be_unique():
    branches = {
        "source_action_index": 0,
        "source_result_field": "state",
        "options": [
            {
                "expected_value": 1,
                "action": {
                    "tool_name": "create_item",
                    "arguments": {},
                },
            },
            {
                "expected_value": 1.0,
                "action": {
                    "tool_name": "inspect_item",
                    "arguments": {},
                },
            },
        ],
    }

    with pytest.raises(
        ValidationError,
        match="expected_branches",
    ):
        make_task(
            tool_results=[
                {
                    "tool_name": "check_item",
                    "result": {
                        "state": 1,
                    },
                },
            ],
            expected_branches=branches,
        )
