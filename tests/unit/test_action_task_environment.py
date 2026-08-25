import json

from observer.core.action_task_environment import (
    ActionTaskEnvironment,
)
from observer.core.observed_action_sequence_evidence import (
    ObservedActionSequenceEvidenceCollector,
)
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)
from schemas.target import TargetCapability


def make_task() -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-action-environment-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Call the appropriate available tool.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="tool-called",
                description="A tool call was observed.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-name-match",
                description="The observed tool name matches.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-arguments-match",
                description="The observed arguments match.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-call-count-match",
                description="The observed call count matches.",
            ),
        ],
        available_tools=[
            {
                "tool_name": "record_item",
                "description": "Record one item.",
                "parameters": {
                    "name": "string",
                    "count": "integer",
                },
            },
        ],
        expected_action={
            "tool_name": "record_item",
            "arguments": {
                "name": "delta",
                "count": 4,
            },
            "call_count": 1,
        },
    )


def test_action_task_environment_exposes_runtime_tool_metadata():
    task = make_task()

    with ActionTaskEnvironment(
        task,
    ) as environment:
        assert task.expected_action is not None

        assert environment.metadata == {
            "dllo_action_gateway": {
                "schema_version": "0.1",
                "tools": [
                    {
                        "tool_name": "record_item",
                        "description": "Record one item.",
                        "parameters": {
                            "name": "string",
                            "count": "integer",
                        },
                        "endpoint": (
                            environment.gateway.tool_url(
                                "record_item"
                            )
                        ),
                        "authorization": {
                            "scheme": "bearer",
                            "token": environment.gateway.token,
                        },
                    },
                ],
            },
        }

        assert (
            environment.collector.expected_action
            == task.expected_action
        )


def test_action_task_environment_does_not_expose_expected_action():
    task = make_task()

    with ActionTaskEnvironment(
        task,
    ) as environment:
        metadata_text = str(environment.metadata)

        assert "expected_action" not in metadata_text
        assert '"name": "delta"' not in metadata_text
        assert "call_count" not in metadata_text


def make_sequence_task() -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-action-sequence-environment-001",
        benchmark_version="0.1",
        evaluator_id="deterministic-evidence-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Persist delta, then inspect it.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="tool-calls-observed",
                description="Tool calls were observed.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-sequence-length-match",
                description="Sequence length matches.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-sequence-order-match",
                description="Sequence order matches.",
            ),
            BenchmarkSuccessCriterion(
                criterion_id="tool-sequence-arguments-match",
                description="Sequence arguments match.",
            ),
        ],
        available_tools=[
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
        expected_actions=[
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
        ],
    )


def test_action_task_environment_supports_expected_action_sequence():
    task = make_sequence_task()

    with ActionTaskEnvironment(task) as environment:
        assert isinstance(
            environment.collector,
            ObservedActionSequenceEvidenceCollector,
        )

        assert task.expected_actions is not None
        assert (
            environment.collector.expected_actions
            == tuple(task.expected_actions)
        )

        tools = environment.metadata[
            "dllo_action_gateway"
        ]["tools"]

        assert [
            tool["tool_name"]
            for tool in tools
        ] == [
            "record_item",
            "inspect_item",
        ]

        metadata_text = json.dumps(
            environment.metadata,
            sort_keys=True,
        )

        assert "expected_action" not in metadata_text
        assert "expected_actions" not in metadata_text
        assert '"delta"' not in metadata_text
