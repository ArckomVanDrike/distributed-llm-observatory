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
    expected_branch=_DEFAULT,
    expected_actions=_DEFAULT,
    tool_results=_DEFAULT,
) -> BenchmarkTask:
    if expected_actions is _DEFAULT:
        expected_actions = [
            {
                "tool_name": "check_item",
                "arguments": {
                    "name": "delta",
                },
            },
            {
                "tool_name": "create_item",
                "arguments": {
                    "name": "delta",
                    "count": 4,
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

    if expected_branch is _DEFAULT:
        expected_branch = {
            "source_action_index": 0,
            "source_result_field": "state",
            "expected_value": "missing",
            "branch_action_index": 1,
        }

    return BenchmarkTask(
        task_id="agent-conditional-branch-001",
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
                    "The expected runtime-dependent "
                    "branch was selected."
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
                "description": "Inspect an existing item.",
                "parameters": {
                    "name": "string",
                },
            },
        ],
        tool_results=tool_results,
        expected_actions=expected_actions,
        expected_branch=expected_branch,
    )


def test_task_accepts_expected_branch():
    task = make_task()

    assert task.expected_branch is not None
    assert task.expected_branch.source_action_index == 0
    assert task.expected_branch.source_result_field == "state"
    assert task.expected_branch.expected_value == "missing"
    assert task.expected_branch.branch_action_index == 1


def test_expected_branch_round_trips():
    task = make_task()

    restored = BenchmarkTask.model_validate(
        task.model_dump()
    )

    assert restored.expected_branch == task.expected_branch


def test_expected_branch_requires_expected_actions():
    with pytest.raises(
        ValidationError,
        match="expected_branch",
    ):
        make_task(
            expected_actions=None,
        )


def test_expected_branch_requires_tool_results():
    with pytest.raises(
        ValidationError,
        match="expected_branch",
    ):
        make_task(
            tool_results=[],
        )


def test_expected_branch_indices_must_exist():
    with pytest.raises(
        ValidationError,
        match="expected_branch",
    ):
        make_task(
            expected_branch={
                "source_action_index": 0,
                "source_result_field": "state",
                "expected_value": "missing",
                "branch_action_index": 2,
            },
        )


def test_expected_branch_must_point_forward():
    with pytest.raises(
        ValidationError,
        match="expected_branch",
    ):
        make_task(
            expected_branch={
                "source_action_index": 1,
                "source_result_field": "state",
                "expected_value": "missing",
                "branch_action_index": 0,
            },
        )


def test_expected_branch_source_field_must_exist():
    with pytest.raises(
        ValidationError,
        match="expected_branch",
    ):
        make_task(
            expected_branch={
                "source_action_index": 0,
                "source_result_field": "missing_field",
                "expected_value": "missing",
                "branch_action_index": 1,
            },
        )


def test_expected_branch_value_must_match_configured_result():
    with pytest.raises(
        ValidationError,
        match="expected_branch",
    ):
        make_task(
            expected_branch={
                "source_action_index": 0,
                "source_result_field": "state",
                "expected_value": "present",
                "branch_action_index": 1,
            },
        )
