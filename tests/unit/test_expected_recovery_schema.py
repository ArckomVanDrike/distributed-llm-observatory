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
    expected_recovery=_DEFAULT,
    expected_actions=_DEFAULT,
    tool_failures=_DEFAULT,
) -> BenchmarkTask:
    if expected_actions is _DEFAULT:
        expected_actions = [
            {
                "tool_name": "persist_primary",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
            {
                "tool_name": "persist_fallback",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
        ]

    if tool_failures is _DEFAULT:
        tool_failures = [
            {
                "tool_name": "persist_primary",
                "status_code": 503,
                "error": {
                    "code": "temporary_unavailable",
                },
            },
        ]

    if expected_recovery is _DEFAULT:
        expected_recovery = {
            "failed_action_index": 0,
            "recovery_action_index": 1,
        }

    return BenchmarkTask(
        task_id="agent-recovery-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task=(
            "Persist an item using the available tools "
            "and recover if necessary."
        ),
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="tool-failure-observed",
                description=(
                    "The configured tool failure was observed."
                ),
            ),
            BenchmarkSuccessCriterion(
                criterion_id="recovery-after-failure",
                description=(
                    "A recovery action followed the failed action."
                ),
            ),
        ],
        available_tools=[
            {
                "tool_name": "persist_primary",
                "description": (
                    "Persist using the primary backend."
                ),
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
            {
                "tool_name": "persist_fallback",
                "description": (
                    "Persist using the fallback backend."
                ),
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
        ],
        tool_failures=tool_failures,
        expected_actions=expected_actions,
        expected_recovery=expected_recovery,
    )


def test_task_accepts_expected_recovery():
    task = make_task()

    assert task.expected_recovery is not None
    assert (
        task.expected_recovery.failed_action_index
        == 0
    )
    assert (
        task.expected_recovery.recovery_action_index
        == 1
    )


def test_expected_recovery_round_trips():
    task = make_task()

    restored = BenchmarkTask.model_validate(
        task.model_dump()
    )

    assert (
        restored.expected_recovery
        == task.expected_recovery
    )


def test_expected_recovery_requires_expected_actions():
    with pytest.raises(
        ValidationError,
        match="expected_recovery",
    ):
        make_task(
            expected_actions=None,
        )


def test_expected_recovery_requires_tool_failures():
    with pytest.raises(
        ValidationError,
        match="expected_recovery",
    ):
        make_task(
            tool_failures=[],
        )


def test_expected_recovery_indices_must_exist():
    with pytest.raises(
        ValidationError,
        match="expected_recovery",
    ):
        make_task(
            expected_recovery={
                "failed_action_index": 0,
                "recovery_action_index": 2,
            },
        )


def test_expected_recovery_must_follow_failure():
    with pytest.raises(
        ValidationError,
        match="expected_recovery",
    ):
        make_task(
            expected_recovery={
                "failed_action_index": 1,
                "recovery_action_index": 0,
            },
        )


def test_expected_recovery_failed_action_must_have_failure():
    with pytest.raises(
        ValidationError,
        match="expected_recovery",
    ):
        make_task(
            tool_failures=[
                {
                    "tool_name": "persist_fallback",
                    "status_code": 503,
                    "error": {
                        "code": "temporary_unavailable",
                    },
                },
            ],
        )


def test_expected_recovery_can_retry_same_tool():
    task = make_task(
        expected_actions=[
            {
                "tool_name": "persist_primary",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
            {
                "tool_name": "persist_primary",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
        ],
    )

    assert (
        task.expected_recovery.recovery_action_index
        == 1
    )
