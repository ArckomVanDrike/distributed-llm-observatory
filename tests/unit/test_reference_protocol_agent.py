from pathlib import Path

from observer.core.action_task_environment import (
    ActionTaskEnvironment,
)
from observer.core.suite_bank import SuiteBank
from observer.core.suite_registry import SuiteRegistry
from observer.core.task_bank import TaskBank
from observer.reference_protocol_agent import (
    ReferenceProtocolAgent,
)


def _protocol_task(task_id: str):
    registry = SuiteRegistry(
        suite_bank=SuiteBank(
            Path("benchmark/suites"),
        ),
        task_bank=TaskBank(
            Path("benchmark/tasks"),
        ),
    )

    resolved = registry.resolve(
        suite_id="agent-protocol-core",
        suite_version="1.0",
    )

    return next(
        task
        for task in resolved.tasks
        if task.task_id == task_id
    )


def test_reference_protocol_agent_manifest():
    agent = ReferenceProtocolAgent()

    manifest = agent.manifest()

    assert manifest == {
        "schema_version": "0.1",
        "target_id": "dllo-reference-protocol-agent",
        "display_name": "DLLO Reference Protocol Agent",
        "target_type": "agent",
        "capabilities": [
            "text",
            "tools",
        ],
    }


def test_reference_protocol_agent_handles_smoke_task():
    agent = ReferenceProtocolAgent()

    result = agent.execute(
        task=(
            "Return exactly DLLO-AGENT-SMOKE-001 "
            "and no additional characters."
        ),
        metadata=None,
    )

    assert result.task_completed is True
    assert result.output_text == (
        "DLLO-AGENT-SMOKE-001"
    )


def test_reference_protocol_agent_handles_instruction_task():
    agent = ReferenceProtocolAgent()

    result = agent.execute(
        task=(
            "Sort these four tokens in ascending ASCII "
            "order: delta, alpha, charlie, bravo. "
            "Return exactly one comma-separated line "
            "with no spaces and no additional characters."
        ),
        metadata=None,
    )

    assert result.task_completed is True
    assert result.output_text == (
        "alpha,bravo,charlie,delta"
    )


def test_reference_protocol_agent_handles_structured_output_task():
    agent = ReferenceProtocolAgent()

    result = agent.execute(
        task=(
            "Return only one JSON object with exactly "
            "these keys and values: name is delta, "
            "count is 4, and active is true. "
            "Do not include Markdown fences, commentary, "
            "or additional keys."
        ),
        metadata=None,
    )

    assert result.task_completed is True
    assert result.output_text == (
        '{"name":"delta","count":4,"active":true}'
    )



def test_reference_protocol_agent_calls_record_item():
    agent = ReferenceProtocolAgent()
    task = _protocol_task(
        "agent-protocol-action-001"
    )

    with ActionTaskEnvironment(task) as environment:
        result = agent.execute(
            task=task.task,
            metadata=environment.metadata,
        )

        calls = environment.gateway.calls

    assert result.task_completed is True
    assert result.output_text is None

    assert len(calls) == 1
    assert calls[0].tool_name == "record_item"
    assert calls[0].arguments == {
        "name": "delta",
        "count": 4,
    }


def test_reference_protocol_agent_selects_record_item():
    agent = ReferenceProtocolAgent()
    task = _protocol_task(
        "agent-protocol-tool-selection-001"
    )

    with ActionTaskEnvironment(task) as environment:
        result = agent.execute(
            task=task.task,
            metadata=environment.metadata,
        )

        calls = environment.gateway.calls

    assert result.task_completed is True
    assert result.output_text is None

    assert len(calls) == 1
    assert calls[0].tool_name == "record_item"
    assert calls[0].arguments == {
        "name": "delta",
        "count": 4,
    }


def test_reference_protocol_agent_runs_action_sequence():
    agent = ReferenceProtocolAgent()
    task = _protocol_task(
        "agent-protocol-action-sequence-001"
    )

    with ActionTaskEnvironment(task) as environment:
        result = agent.execute(
            task=task.task,
            metadata=environment.metadata,
        )

        calls = environment.gateway.calls

    assert result.task_completed is True
    assert result.output_text is None

    assert len(calls) == 2

    assert calls[0].tool_name == "record_item"
    assert calls[0].arguments == {
        "name": "delta",
        "count": 4,
    }

    assert calls[1].tool_name == "inspect_item"
    assert calls[1].arguments == {
        "name": "delta",
    }


def test_reference_protocol_agent_propagates_runtime_tool_result():
    agent = ReferenceProtocolAgent()

    canonical_task = _protocol_task(
        "agent-protocol-data-flow-001"
    )

    runtime_task = canonical_task.model_copy(
        update={
            "tool_results": [
                canonical_task.tool_results[
                    0
                ].model_copy(
                    update={
                        "result": {
                            "item_id": (
                                "item-runtime-999"
                            ),
                        },
                    },
                ),
            ],
        },
    )

    with ActionTaskEnvironment(
        runtime_task
    ) as environment:
        result = agent.execute(
            task=runtime_task.task,
            metadata=environment.metadata,
        )

        calls = environment.gateway.calls

    assert result.task_completed is True
    assert result.output_text is None

    assert len(calls) == 2

    assert calls[0].tool_name == "create_item"
    assert calls[0].arguments == {
        "name": "delta",
        "count": 4,
    }

    assert calls[1].tool_name == "inspect_item"
    assert calls[1].arguments == {
        "item_id": "item-runtime-999",
    }


def test_reference_protocol_agent_recovers_from_runtime_tool_failure():
    agent = ReferenceProtocolAgent()

    canonical_task = _protocol_task(
        "agent-protocol-recovery-001"
    )

    runtime_task = canonical_task.model_copy(
        update={
            "tool_failures": [
                canonical_task.tool_failures[
                    0
                ].model_copy(
                    update={
                        "status_code": 429,
                        "error": {
                            "code": (
                                "runtime_rate_limited"
                            ),
                        },
                    },
                ),
            ],
        },
    )

    with ActionTaskEnvironment(
        runtime_task
    ) as environment:
        result = agent.execute(
            task=runtime_task.task,
            metadata=environment.metadata,
        )

        calls = environment.gateway.calls
        outcomes = environment.gateway.outcomes

    assert result.task_completed is True
    assert result.output_text is None

    assert len(calls) == 2

    assert calls[0].tool_name == "persist_primary"
    assert calls[0].arguments == {
        "name": "delta",
        "count": 4,
    }

    assert calls[1].tool_name == "persist_fallback"
    assert calls[1].arguments == {
        "name": "delta",
        "count": 4,
    }

    assert len(outcomes) == 2
    assert outcomes[0].status_code == 429
    assert outcomes[0].succeeded is False
    assert outcomes[1].status_code == 200
    assert outcomes[1].succeeded is True


def test_reference_protocol_agent_selects_branch_from_runtime_state():
    agent = ReferenceProtocolAgent()
    task = _protocol_task(
        "agent-protocol-branch-001"
    )

    with ActionTaskEnvironment(task) as environment:
        result = agent.execute(
            task=task.task,
            metadata=environment.metadata,
        )

        calls = environment.gateway.calls
        outcomes = environment.gateway.outcomes

    assert result.task_completed is True
    assert result.output_text is None

    assert len(calls) == 2

    assert calls[0].tool_name == "check_item"
    assert calls[0].arguments == {
        "name": "delta",
    }

    assert outcomes[0].result == {
        "state": "missing",
    }

    assert calls[1].tool_name == "create_item"
    assert calls[1].arguments == {
        "name": "delta",
        "count": 4,
    }


def test_reference_protocol_agent_selects_multi_branch_from_runtime_state():
    agent = ReferenceProtocolAgent()

    cases = [
        (
            "agent-protocol-multi-branch-001",
            "missing",
            "create_item",
            {
                "name": "delta",
                "count": 4,
            },
        ),
        (
            "agent-protocol-multi-branch-002",
            "present",
            "inspect_item",
            {
                "name": "delta",
            },
        ),
    ]

    for (
        task_id,
        expected_state,
        expected_tool,
        expected_arguments,
    ) in cases:
        task = _protocol_task(task_id)

        with ActionTaskEnvironment(task) as environment:
            result = agent.execute(
                task=task.task,
                metadata=environment.metadata,
            )

            calls = environment.gateway.calls
            outcomes = environment.gateway.outcomes

        assert result.task_completed is True
        assert result.output_text is None

        assert len(calls) == 2

        assert calls[0].tool_name == "check_item"
        assert calls[0].arguments == {
            "name": "delta",
        }

        assert outcomes[0].result == {
            "state": expected_state,
        }

        assert calls[1].tool_name == expected_tool
        assert calls[1].arguments == expected_arguments
