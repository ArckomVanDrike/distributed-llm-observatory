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
    tool_failures,
    tool_results=None,
    available_tools=None,
    required_capabilities=None,
) -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-tool-failure-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Persist an item using the available tools.",
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
                criterion_id="tool-failure-observed",
                description=(
                    "A configured tool failure was observed."
                ),
            ),
        ],
        available_tools=(
            available_tools
            if available_tools is not None
            else [
                {
                    "tool_name": "persist_primary",
                    "description": "Persist using the primary backend.",
                    "parameters": {
                        "name": "string",
                        "count": "integer",
                    },
                },
                {
                    "tool_name": "persist_fallback",
                    "description": "Persist using a fallback backend.",
                    "parameters": {
                        "name": "string",
                        "count": "integer",
                    },
                },
            ]
        ),
        tool_results=(
            tool_results
            if tool_results is not None
            else []
        ),
        tool_failures=tool_failures,
    )


def primary_failure():
    return {
        "tool_name": "persist_primary",
        "status_code": 503,
        "error": {
            "code": "temporary_unavailable",
        },
    }


def test_task_accepts_deterministic_tool_failure():
    task = make_task(
        tool_failures=[
            primary_failure(),
        ],
    )

    assert len(task.tool_failures) == 1

    failure = task.tool_failures[0]

    assert failure.tool_name == "persist_primary"
    assert failure.status_code == 503
    assert failure.error == {
        "code": "temporary_unavailable",
    }


def test_tool_failure_round_trips():
    task = make_task(
        tool_failures=[
            primary_failure(),
        ],
    )

    restored = BenchmarkTask.model_validate(
        task.model_dump()
    )

    assert (
        restored.tool_failures
        == task.tool_failures
    )


def test_tool_failures_require_tools_capability():
    with pytest.raises(
        ValidationError,
        match="tool_failures",
    ):
        make_task(
            tool_failures=[
                primary_failure(),
            ],
            required_capabilities={
                TargetCapability.TEXT,
            },
        )


def test_tool_failures_require_available_tools():
    with pytest.raises(
        ValidationError,
        match="tool_failures",
    ):
        make_task(
            tool_failures=[
                primary_failure(),
            ],
            available_tools=[],
        )


def test_tool_failure_tool_must_be_available():
    failure = primary_failure()
    failure["tool_name"] = "missing_tool"

    with pytest.raises(
        ValidationError,
        match="tool_failures",
    ):
        make_task(
            tool_failures=[
                failure,
            ],
        )


def test_tool_failure_tool_names_must_be_unique():
    with pytest.raises(
        ValidationError,
        match="tool_failures",
    ):
        make_task(
            tool_failures=[
                primary_failure(),
                primary_failure(),
            ],
        )


def test_tool_failure_status_must_be_error_status():
    failure = primary_failure()
    failure["status_code"] = 200

    with pytest.raises(
        ValidationError,
        match="status_code",
    ):
        make_task(
            tool_failures=[
                failure,
            ],
        )


def test_tool_cannot_have_result_and_failure():
    with pytest.raises(
        ValidationError,
        match="tool_results.*tool_failures|tool_failures.*tool_results",
    ):
        make_task(
            tool_results=[
                {
                    "tool_name": "persist_primary",
                    "result": {
                        "stored": True,
                    },
                },
            ],
            tool_failures=[
                primary_failure(),
            ],
        )
