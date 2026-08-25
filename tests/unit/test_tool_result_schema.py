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
    tool_results,
    available_tools=None,
    required_capabilities=None,
) -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-tool-result-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Create an item, then inspect it.",
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
                criterion_id="tool-result-used",
                description=(
                    "A tool result was used by a later action."
                ),
            ),
        ],
        available_tools=(
            available_tools
            if available_tools is not None
            else [
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
            ]
        ),
        tool_results=tool_results,
    )


def test_task_accepts_deterministic_tool_result():
    task = make_task(
        tool_results=[
            {
                "tool_name": "create_item",
                "result": {
                    "item_id": "item-742",
                },
            },
        ],
    )

    assert len(task.tool_results) == 1
    assert (
        task.tool_results[0].tool_name
        == "create_item"
    )
    assert task.tool_results[0].result == {
        "item_id": "item-742",
    }


def test_tool_result_round_trips():
    task = make_task(
        tool_results=[
            {
                "tool_name": "create_item",
                "result": {
                    "item_id": "item-742",
                    "created": True,
                },
            },
        ],
    )

    restored = BenchmarkTask.model_validate(
        task.model_dump()
    )

    assert (
        restored.tool_results
        == task.tool_results
    )


def test_tool_results_require_tools_capability():
    with pytest.raises(
        ValidationError,
        match="tool_results",
    ):
        make_task(
            tool_results=[
                {
                    "tool_name": "create_item",
                    "result": {
                        "item_id": "item-742",
                    },
                },
            ],
            required_capabilities={
                TargetCapability.TEXT,
            },
        )


def test_tool_results_require_available_tools():
    with pytest.raises(
        ValidationError,
        match="tool_results",
    ):
        make_task(
            tool_results=[
                {
                    "tool_name": "create_item",
                    "result": {
                        "item_id": "item-742",
                    },
                },
            ],
            available_tools=[],
        )


def test_tool_result_tool_must_be_available():
    with pytest.raises(
        ValidationError,
        match="tool_results",
    ):
        make_task(
            tool_results=[
                {
                    "tool_name": "delete_item",
                    "result": {
                        "deleted": True,
                    },
                },
            ],
        )


def test_tool_result_tool_names_must_be_unique():
    with pytest.raises(
        ValidationError,
        match="tool_results",
    ):
        make_task(
            tool_results=[
                {
                    "tool_name": "create_item",
                    "result": {
                        "item_id": "item-742",
                    },
                },
                {
                    "tool_name": "create_item",
                    "result": {
                        "item_id": "item-999",
                    },
                },
            ],
        )
