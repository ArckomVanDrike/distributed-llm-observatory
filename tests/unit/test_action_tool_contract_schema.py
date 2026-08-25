import pytest
from pydantic import ValidationError

from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
    BenchmarkToolContract,
)
from schemas.target import TargetCapability


def record_item_tool() -> BenchmarkToolContract:
    return BenchmarkToolContract(
        tool_name="record_item",
        description="Record one item.",
        parameters={
            "name": "string",
            "count": "integer",
        },
    )


def make_task(
    *,
    available_tools,
    expected_tool_name: str = "record_item",
    required_capabilities=None,
) -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-tool-contract-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Call the appropriate available tool.",
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
                description="A tool call was observed.",
            ),
        ],
        available_tools=available_tools,
        expected_action={
            "tool_name": expected_tool_name,
            "arguments": {
                "name": "delta",
                "count": 4,
            },
            "call_count": 1,
        },
    )


def test_benchmark_tool_contract_accepts_parameter_types():
    tool = record_item_tool()

    assert tool.tool_name == "record_item"
    assert tool.description == "Record one item."
    assert tool.parameters == {
        "name": "string",
        "count": "integer",
    }


def test_action_task_accepts_available_tools():
    task = make_task(
        available_tools=[
            record_item_tool(),
        ],
    )

    assert [
        tool.tool_name
        for tool in task.available_tools
    ] == [
        "record_item",
    ]


def test_expected_action_requires_available_tool():
    with pytest.raises(
        ValidationError,
        match="available_tools",
    ):
        make_task(
            available_tools=[],
        )


def test_expected_action_tool_must_be_available():
    with pytest.raises(
        ValidationError,
        match="expected_action tool_name",
    ):
        make_task(
            available_tools=[
                record_item_tool(),
            ],
            expected_tool_name="delete_item",
        )


def test_available_tools_require_tools_capability():
    with pytest.raises(
        ValidationError,
        match="tools capability",
    ):
        make_task(
            available_tools=[
                record_item_tool(),
            ],
            required_capabilities={
                TargetCapability.TEXT,
            },
        )


def test_available_tools_reject_duplicate_tool_names():
    with pytest.raises(
        ValidationError,
        match="unique",
    ):
        make_task(
            available_tools=[
                record_item_tool(),
                record_item_tool(),
            ],
        )
