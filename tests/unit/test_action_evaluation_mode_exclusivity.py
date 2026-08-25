from itertools import combinations

import pytest
from pydantic import ValidationError

from schemas.benchmark import BenchmarkTask

ADVANCED_MODES = {
    "expected_propagations": [
        {
            "source_action_index": 0,
            "source_result_field": "count",
            "target_action_index": 1,
            "target_argument": "count",
        },
    ],
    "expected_recovery": {
        "failed_action_index": 1,
        "recovery_action_index": 2,
    },
    "expected_branch": {
        "source_action_index": 0,
        "source_result_field": "state",
        "expected_value": "missing",
        "branch_action_index": 1,
    },
    "expected_branches": {
        "source_action_index": 0,
        "source_result_field": "state",
        "options": [
            {
                "expected_value": "missing",
                "action": {
                    "tool_name": "persist_item",
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
    },
}


def make_task(**mode_fields):
    payload = {
        "schema_version": "0.1",
        "task_id": "evaluation-mode-test",
        "benchmark_version": "0.1",
        "evaluator_id": "deterministic-evidence-v0-1",
        "family": "agent",
        "category": "technical",
        "difficulty": "easy",
        "task": "Handle item delta.",
        "required_capabilities": [
            "text",
            "tools",
        ],
        "success_criteria": [
            {
                "criterion_id": "tool-calls-observed",
                "description": "Tool calls were observed.",
            },
        ],
        "available_tools": [
            {
                "tool_name": "check_item",
                "description": "Check an item.",
                "parameters": {
                    "name": "string",
                },
            },
            {
                "tool_name": "persist_item",
                "description": "Persist an item.",
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
            {
                "tool_name": "fallback_item",
                "description": "Persist via fallback.",
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
        "tool_results": [
            {
                "tool_name": "check_item",
                "result": {
                    "state": "missing",
                    "count": 4,
                },
            },
        ],
        "tool_failures": [
            {
                "tool_name": "persist_item",
                "status_code": 503,
                "error": {
                    "code": "temporary_unavailable",
                },
            },
        ],
        "expected_actions": [
            {
                "tool_name": "check_item",
                "arguments": {
                    "name": "delta",
                },
            },
            {
                "tool_name": "persist_item",
                "arguments": {
                    "name": "delta",
                },
            },
            {
                "tool_name": "fallback_item",
                "arguments": {
                    "name": "delta",
                    "count": 4,
                },
            },
        ],
        **mode_fields,
    }

    return BenchmarkTask.model_validate(payload)


@pytest.mark.parametrize(
    ("first_mode", "second_mode"),
    list(combinations(ADVANCED_MODES, 2)),
)
def test_action_evaluation_modes_are_mutually_exclusive(
    first_mode,
    second_mode,
):
    with pytest.raises(
        ValidationError,
        match="evaluation modes",
    ):
        make_task(
            **{
                first_mode: ADVANCED_MODES[first_mode],
                second_mode: ADVANCED_MODES[second_mode],
            }
        )


@pytest.mark.parametrize(
    "mode_name",
    ADVANCED_MODES,
)
def test_each_action_evaluation_mode_is_valid_alone(
    mode_name,
):
    task = make_task(
        **{
            mode_name: ADVANCED_MODES[mode_name],
        }
    )

    assert getattr(task, mode_name) is not None
