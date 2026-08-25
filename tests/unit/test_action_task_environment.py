import json
from urllib.request import Request, urlopen

from observer.core.action_task_environment import (
    ActionTaskEnvironment,
)
from observer.core.observed_action_data_flow_evidence import (
    ObservedActionDataFlowEvidenceCollector,
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


def test_action_task_environment_wires_tool_results_to_gateway():
    base_task = make_sequence_task()

    task = BenchmarkTask.model_validate(
        {
            **base_task.model_dump(),
            "tool_results": [
                {
                    "tool_name": "record_item",
                    "result": {
                        "item_id": "item-742",
                    },
                },
            ],
        }
    )

    with ActionTaskEnvironment(task) as environment:
        metadata_text = json.dumps(
            environment.metadata,
            sort_keys=True,
        )

        assert "tool_results" not in metadata_text
        assert "item-742" not in metadata_text

        request = Request(
            environment.gateway.tool_url(
                "record_item"
            ),
            data=json.dumps(
                {
                    "name": "delta",
                    "count": 4,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": (
                    "Bearer "
                    + environment.gateway.token
                ),
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(
            request,
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200
        assert payload == {
            "schema_version": "0.1",
            "accepted": True,
            "result": {
                "item_id": "item-742",
            },
        }

        assert len(environment.gateway.calls) == 1
        assert (
            environment.gateway.calls[0].tool_name
            == "record_item"
        )


def make_data_flow_task() -> BenchmarkTask:
    return BenchmarkTask(
        task_id="agent-data-flow-environment-001",
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
            BenchmarkSuccessCriterion(
                criterion_id="tool-result-propagated",
                description="Tool result was propagated.",
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
        tool_results=[
            {
                "tool_name": "create_item",
                "result": {
                    "item_id": "item-742",
                },
            },
        ],
        expected_actions=[
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
        ],
        expected_propagations=[
            {
                "source_action_index": 0,
                "source_result_field": "item_id",
                "target_action_index": 1,
                "target_argument": "item_id",
            },
        ],
    )


def test_action_task_environment_uses_data_flow_collector():
    task = make_data_flow_task()

    with ActionTaskEnvironment(task) as environment:
        assert isinstance(
            environment.collector,
            ObservedActionDataFlowEvidenceCollector,
        )

        assert task.expected_actions is not None
        assert task.expected_propagations is not None

        assert (
            environment.collector.expected_actions
            == tuple(task.expected_actions)
        )
        assert (
            environment.collector.tool_results
            == tuple(task.tool_results)
        )
        assert (
            environment.collector.expected_propagations
            == tuple(task.expected_propagations)
        )

        metadata_text = json.dumps(
            environment.metadata,
            sort_keys=True,
        )

        assert "tool_results" not in metadata_text
        assert "expected_propagations" not in metadata_text
        assert "item-742" not in metadata_text


def test_action_task_environment_wires_tool_failures_to_gateway():
    from urllib.error import HTTPError

    base_task = make_sequence_task()

    task = BenchmarkTask.model_validate(
        {
            **base_task.model_dump(),
            "tool_failures": [
                {
                    "tool_name": "record_item",
                    "status_code": 503,
                    "error": {
                        "code": "temporary_unavailable",
                    },
                },
            ],
        }
    )

    with ActionTaskEnvironment(task) as environment:
        metadata_text = json.dumps(
            environment.metadata,
            sort_keys=True,
        )

        assert "tool_failures" not in metadata_text
        assert "temporary_unavailable" not in metadata_text
        assert "503" not in metadata_text

        request = Request(
            environment.gateway.tool_url(
                "record_item"
            ),
            data=json.dumps(
                {
                    "name": "delta",
                    "count": 4,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": (
                    "Bearer "
                    + environment.gateway.token
                ),
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            urlopen(
                request,
                timeout=2,
            )
        except HTTPError as exc:
            payload = json.loads(
                exc.read().decode("utf-8")
            )
            assert exc.code == 503
        else:
            raise AssertionError(
                "Expected configured tool failure."
            )

        assert payload == {
            "schema_version": "0.1",
            "accepted": True,
            "error": {
                "code": "temporary_unavailable",
            },
        }

        assert len(environment.gateway.calls) == 1
        assert (
            environment.gateway.calls[0].tool_name
            == "record_item"
        )


def test_action_task_environment_uses_recovery_collector():
    from observer.core.observed_action_recovery_evidence import (
        ObservedActionRecoveryEvidenceCollector,
    )

    base_task = make_sequence_task()

    task = BenchmarkTask.model_validate(
        {
            **base_task.model_dump(),
            "tool_failures": [
                {
                    "tool_name": "record_item",
                    "status_code": 503,
                    "error": {
                        "code": "temporary_unavailable",
                    },
                },
            ],
            "expected_recovery": {
                "failed_action_index": 0,
                "recovery_action_index": 1,
            },
        }
    )

    with ActionTaskEnvironment(task) as environment:
        assert isinstance(
            environment.collector,
            ObservedActionRecoveryEvidenceCollector,
        )

        assert (
            environment.collector.expected_actions
            == tuple(task.expected_actions)
        )
        assert (
            environment.collector.tool_failures
            == tuple(task.tool_failures)
        )
        assert (
            environment.collector.expected_recovery
            == task.expected_recovery
        )

        metadata_text = json.dumps(
            environment.metadata,
            sort_keys=True,
        )

        assert "expected_recovery" not in metadata_text
        assert "tool_failures" not in metadata_text
        assert "temporary_unavailable" not in metadata_text
        assert "503" not in metadata_text


def test_action_task_environment_uses_branch_collector():
    from observer.core.observed_action_branch_evidence import (
        ObservedActionBranchEvidenceCollector,
    )

    base_task = make_sequence_task()

    task = BenchmarkTask.model_validate(
        {
            **base_task.model_dump(),
            "available_tools": [
                {
                    "tool_name": "record_item",
                    "description": (
                        "Record an item and return its state."
                    ),
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
                    "tool_name": "record_item",
                    "result": {
                        "state": "missing",
                    },
                },
            ],
            "expected_branch": {
                "source_action_index": 0,
                "source_result_field": "state",
                "expected_value": "missing",
                "branch_action_index": 1,
            },
        }
    )

    with ActionTaskEnvironment(task) as environment:
        assert isinstance(
            environment.collector,
            ObservedActionBranchEvidenceCollector,
        )

        assert (
            environment.collector.expected_actions
            == tuple(task.expected_actions)
        )
        assert (
            environment.collector.tool_results
            == tuple(task.tool_results)
        )
        assert (
            environment.collector.expected_branch
            == task.expected_branch
        )

        metadata_text = json.dumps(
            environment.metadata,
            sort_keys=True,
        )

        assert "expected_branch" not in metadata_text
        assert "tool_results" not in metadata_text
        assert '"state": "missing"' not in metadata_text


def test_action_task_environment_uses_multi_branch_collector():
    from observer.core.observed_action_multi_branch_evidence import (
        ObservedActionMultiBranchEvidenceCollector,
    )

    base_task = make_sequence_task()

    task = BenchmarkTask.model_validate(
        {
            **base_task.model_dump(),
            "available_tools": [
                {
                    "tool_name": "record_item",
                    "description": (
                        "Return the current item state."
                    ),
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
                {
                    "tool_name": "fallback_item",
                    "description": "Fallback item action.",
                    "parameters": {
                        "name": "string",
                    },
                },
            ],
            "tool_results": [
                {
                    "tool_name": "record_item",
                    "result": {
                        "state": "missing",
                    },
                },
            ],
            "expected_actions": [
                {
                    "tool_name": "record_item",
                    "arguments": {
                        "name": "delta",
                        "count": 4,
                    },
                },
            ],
            "expected_branches": {
                "source_action_index": 0,
                "source_result_field": "state",
                "options": [
                    {
                        "expected_value": "missing",
                        "action": {
                            "tool_name": "inspect_item",
                            "arguments": {
                                "name": "delta",
                            },
                        },
                    },
                    {
                        "expected_value": "present",
                        "action": {
                            "tool_name": "fallback_item",
                            "arguments": {
                                "name": "delta",
                            },
                        },
                    },
                ],
            },
        }
    )

    with ActionTaskEnvironment(task) as environment:
        assert isinstance(
            environment.collector,
            ObservedActionMultiBranchEvidenceCollector,
        )

        assert (
            environment.collector.expected_actions
            == tuple(task.expected_actions)
        )
        assert (
            environment.collector.expected_branches
            == task.expected_branches
        )

        metadata_text = json.dumps(
            environment.metadata,
            sort_keys=True,
        )

        assert "expected_branches" not in metadata_text
        assert "tool_results" not in metadata_text
        assert '"state": "missing"' not in metadata_text
        assert '"state": "present"' not in metadata_text
