from pathlib import Path

from observer.core.suite_bank import SuiteBank
from observer.core.suite_registry import SuiteRegistry
from observer.core.task_bank import TaskBank
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkFamily,
    BenchmarkHarnessProfile,
)
from schemas.target import TargetCapability


def test_canonical_agent_protocol_smoke_task():
    tasks = TaskBank(
        Path("benchmark/tasks")
    ).load_all()

    matches = [
        task
        for task in tasks
        if task.task_id == "agent-protocol-smoke-001"
    ]

    assert len(matches) == 1

    task = matches[0]

    assert task.benchmark_version == "0.1"
    assert task.family.value == "agent"
    assert task.evaluator_id == "exact-output-v0-1"
    assert task.fixture_id is None
    assert task.expected_output_text == "DLLO-AGENT-SMOKE-001"
    assert {
        capability.value
        for capability in task.required_capabilities
    } == {
        "text",
    }

    assert [
        criterion.criterion_id
        for criterion in task.success_criteria
    ] == [
        "output-exact-match",
    ]


def test_canonical_agent_protocol_suite():
    suites = SuiteBank(
        Path("benchmark/suites")
    ).load_all()

    matches = [
        suite
        for suite in suites
        if (
            suite.suite_id == "agent-protocol-core"
            and suite.suite_version == "0.1"
        )
    ]

    assert len(matches) == 1

    suite = matches[0]

    assert suite.family.value == "agent"
    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )
    assert suite.task_ids == [
        "agent-protocol-smoke-001",
    ]
    assert suite.enabled is False



def test_canonical_agent_protocol_instruction_task():
    tasks = TaskBank(
        Path("benchmark/tasks")
    ).load_all()

    matches = [
        task
        for task in tasks
        if task.task_id == "agent-protocol-instruction-001"
    ]

    assert len(matches) == 1

    task = matches[0]

    assert task.benchmark_version == "0.1"
    assert task.family.value == "agent"
    assert task.evaluator_id == "exact-output-v0-1"
    assert task.fixture_id is None
    assert (
        task.expected_output_text
        == "alpha,bravo,charlie,delta"
    )
    assert {
        capability.value
        for capability in task.required_capabilities
    } == {
        "text",
    }

    assert [
        criterion.criterion_id
        for criterion in task.success_criteria
    ] == [
        "output-exact-match",
    ]


def test_canonical_agent_protocol_suite_v0_2():
    suites = SuiteBank(
        Path("benchmark/suites")
    ).load_all()

    matches = [
        suite
        for suite in suites
        if (
            suite.suite_id == "agent-protocol-core"
            and suite.suite_version == "0.2"
        )
    ]

    assert len(matches) == 1

    suite = matches[0]

    assert suite.family.value == "agent"
    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )
    assert suite.task_ids == [
        "agent-protocol-smoke-001",
        "agent-protocol-instruction-001",
    ]
    assert suite.enabled is False



def test_protocol_suite_v0_1_remains_exactly_resolvable():
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
        suite_version="0.1",
    )

    assert resolved.suite.enabled is False
    assert resolved.suite.suite_version == "0.1"
    assert [
        task.task_id
        for task in resolved.tasks
    ] == [
        "agent-protocol-smoke-001",
    ]



def test_canonical_agent_protocol_structured_output_task():
    tasks = TaskBank(
        Path("benchmark/tasks")
    ).load_all()

    matches = [
        task
        for task in tasks
        if (
            task.task_id
            == "agent-protocol-structured-output-001"
        )
    ]

    assert len(matches) == 1

    task = matches[0]

    assert task.benchmark_version == "0.1"
    assert task.family.value == "agent"
    assert (
        task.category.value
        == "instruction_following"
    )
    assert task.evaluator_id == "json-structure-v0-1"
    assert task.fixture_id is None
    assert task.expected_output_text is None
    assert task.expected_output_json_object == {
        "name": "delta",
        "count": 4,
        "active": True,
    }
    assert {
        capability.value
        for capability in task.required_capabilities
    } == {
        "text",
    }

    assert [
        criterion.criterion_id
        for criterion in task.success_criteria
    ] == [
        "json-structure-match",
    ]


def test_canonical_agent_protocol_suite_v0_3():
    suites = SuiteBank(
        Path("benchmark/suites")
    ).load_all()

    matches = [
        suite
        for suite in suites
        if (
            suite.suite_id == "agent-protocol-core"
            and suite.suite_version == "0.3"
        )
    ]

    assert len(matches) == 1

    suite = matches[0]

    assert suite.family.value == "agent"
    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )
    assert suite.task_ids == [
        "agent-protocol-smoke-001",
        "agent-protocol-instruction-001",
        "agent-protocol-structured-output-001",
    ]
    assert suite.enabled is False


def test_canonical_agent_protocol_action_task():
    task_bank = TaskBank(
        Path("benchmark/tasks"),
    )

    matches = [
        task
        for task in task_bank.load_all()
        if task.task_id == "agent-protocol-action-001"
    ]

    assert len(matches) == 1

    task = matches[0]

    assert task.benchmark_version == "0.1"
    assert task.family is BenchmarkFamily.AGENT
    assert (
        task.category
        is BenchmarkCategory.TECHNICAL
    )
    assert (
        task.evaluator_id
        == "deterministic-evidence-v0-1"
    )

    assert task.fixture_id is None
    assert task.expected_output_text is None
    assert task.expected_output_json_object is None

    assert task.required_capabilities == {
        TargetCapability.TEXT,
        TargetCapability.TOOLS,
    }

    assert [
        criterion.criterion_id
        for criterion in task.success_criteria
    ] == [
        "tool-called",
        "tool-name-match",
        "tool-arguments-match",
        "tool-call-count-match",
    ]

    assert len(task.available_tools) == 1

    tool = task.available_tools[0]

    assert tool.tool_name == "record_item"
    assert tool.description == "Record one item."
    assert tool.parameters == {
        "name": "string",
        "count": "integer",
    }

    assert task.expected_action is not None
    assert task.expected_action.tool_name == "record_item"
    assert task.expected_action.arguments == {
        "name": "delta",
        "count": 4,
    }
    assert task.expected_action.call_count == 1


def test_canonical_agent_protocol_suite_v0_4():
    suite_bank = SuiteBank(
        Path("benchmark/suites"),
    )

    matches = [
        suite
        for suite in suite_bank.load_all()
        if (
            suite.suite_id == "agent-protocol-core"
            and suite.suite_version == "0.4"
        )
    ]

    assert len(matches) == 1

    suite = matches[0]

    assert suite.family is BenchmarkFamily.AGENT
    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )

    assert suite.task_ids == [
        "agent-protocol-smoke-001",
        "agent-protocol-instruction-001",
        "agent-protocol-structured-output-001",
        "agent-protocol-action-001",
    ]

    assert suite.enabled is False


def test_protocol_suite_v0_3_remains_exactly_resolvable():
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
        suite_version="0.3",
    )

    assert resolved.suite.suite_version == "0.3"

    assert [
        task.task_id
        for task in resolved.tasks
    ] == [
        "agent-protocol-smoke-001",
        "agent-protocol-instruction-001",
        "agent-protocol-structured-output-001",
    ]


def test_canonical_agent_protocol_tool_selection_task():
    task_bank = TaskBank(
        Path("benchmark/tasks"),
    )

    matches = [
        task
        for task in task_bank.load_all()
        if (
            task.task_id
            == "agent-protocol-tool-selection-001"
        )
    ]

    assert len(matches) == 1

    task = matches[0]

    assert task.benchmark_version == "0.1"
    assert task.family is BenchmarkFamily.AGENT
    assert (
        task.category
        is BenchmarkCategory.TECHNICAL
    )
    assert (
        task.evaluator_id
        == "deterministic-evidence-v0-1"
    )

    assert task.required_capabilities == {
        TargetCapability.TEXT,
        TargetCapability.TOOLS,
    }

    # The task describes the goal, but does not tell
    # the SUT which tool the observer expects.
    assert "record_item" not in task.task

    assert [
        tool.tool_name
        for tool in task.available_tools
    ] == [
        "record_item",
        "inspect_item",
    ]

    assert task.available_tools[0].parameters == {
        "name": "string",
        "count": "integer",
    }
    assert task.available_tools[1].parameters == {
        "name": "string",
    }

    assert task.expected_action is not None
    assert (
        task.expected_action.tool_name
        == "record_item"
    )
    assert task.expected_action.arguments == {
        "name": "delta",
        "count": 4,
    }
    assert task.expected_action.call_count == 1

    assert [
        criterion.criterion_id
        for criterion in task.success_criteria
    ] == [
        "tool-called",
        "tool-name-match",
        "tool-arguments-match",
        "tool-call-count-match",
    ]


def test_canonical_agent_protocol_suite_v0_5():
    suite_bank = SuiteBank(
        Path("benchmark/suites"),
    )

    matches = [
        suite
        for suite in suite_bank.load_all()
        if (
            suite.suite_id == "agent-protocol-core"
            and suite.suite_version == "0.5"
        )
    ]

    assert len(matches) == 1

    suite = matches[0]

    assert suite.family is BenchmarkFamily.AGENT
    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )

    assert suite.task_ids == [
        "agent-protocol-smoke-001",
        "agent-protocol-instruction-001",
        "agent-protocol-structured-output-001",
        "agent-protocol-action-001",
        "agent-protocol-tool-selection-001",
    ]

    assert suite.enabled is False


def test_protocol_suite_v0_4_remains_exactly_resolvable():
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
        suite_version="0.4",
    )

    assert resolved.suite.suite_version == "0.4"

    assert [
        task.task_id
        for task in resolved.tasks
    ] == [
        "agent-protocol-smoke-001",
        "agent-protocol-instruction-001",
        "agent-protocol-structured-output-001",
        "agent-protocol-action-001",
    ]



def test_canonical_agent_protocol_action_sequence_task():
    task_bank = TaskBank(
        Path("benchmark/tasks"),
    )

    matches = [
        task
        for task in task_bank.load_all()
        if (
            task.task_id
            == "agent-protocol-action-sequence-001"
        )
    ]

    assert len(matches) == 1

    task = matches[0]

    assert task.benchmark_version == "0.1"
    assert task.family is BenchmarkFamily.AGENT
    assert (
        task.category
        is BenchmarkCategory.TECHNICAL
    )
    assert (
        task.evaluator_id
        == "deterministic-evidence-v0-1"
    )

    assert task.required_capabilities == {
        TargetCapability.TEXT,
        TargetCapability.TOOLS,
    }

    # The task describes the goal, not the
    # observer's expected tool names.
    assert "record_item" not in task.task
    assert "inspect_item" not in task.task

    assert [
        tool.tool_name
        for tool in task.available_tools
    ] == [
        "record_item",
        "inspect_item",
    ]

    assert task.available_tools[0].parameters == {
        "name": "string",
        "count": "integer",
    }
    assert task.available_tools[1].parameters == {
        "name": "string",
    }

    assert task.expected_action is None
    assert task.expected_actions is not None

    assert [
        action.tool_name
        for action in task.expected_actions
    ] == [
        "record_item",
        "inspect_item",
    ]

    assert task.expected_actions[0].arguments == {
        "name": "delta",
        "count": 4,
    }
    assert task.expected_actions[1].arguments == {
        "name": "delta",
    }

    assert [
        criterion.criterion_id
        for criterion in task.success_criteria
    ] == [
        "tool-calls-observed",
        "tool-sequence-length-match",
        "tool-sequence-order-match",
        "tool-sequence-arguments-match",
    ]

    assert task.enabled is True


def test_canonical_agent_protocol_suite_v0_6():
    suite_bank = SuiteBank(
        Path("benchmark/suites"),
    )

    matches = [
        suite
        for suite in suite_bank.load_all()
        if (
            suite.suite_id == "agent-protocol-core"
            and suite.suite_version == "0.6"
        )
    ]

    assert len(matches) == 1

    suite = matches[0]

    assert suite.family is BenchmarkFamily.AGENT
    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )

    assert suite.task_ids == [
        "agent-protocol-smoke-001",
        "agent-protocol-instruction-001",
        "agent-protocol-structured-output-001",
        "agent-protocol-action-001",
        "agent-protocol-tool-selection-001",
        "agent-protocol-action-sequence-001",
    ]

    assert suite.enabled is False



def test_canonical_agent_protocol_data_flow_task():
    task_bank = TaskBank(
        Path("benchmark/tasks"),
    )

    matches = [
        task
        for task in task_bank.load_all()
        if (
            task.task_id
            == "agent-protocol-data-flow-001"
        )
    ]

    assert len(matches) == 1

    task = matches[0]

    assert task.benchmark_version == "0.1"
    assert task.family is BenchmarkFamily.AGENT
    assert (
        task.category
        is BenchmarkCategory.TECHNICAL
    )
    assert (
        task.evaluator_id
        == "deterministic-evidence-v0-1"
    )

    assert task.required_capabilities == {
        TargetCapability.TEXT,
        TargetCapability.TOOLS,
    }

    # The prompt describes the goal without
    # revealing observer-side tool selection.
    assert "create_item" not in task.task
    assert "inspect_item" not in task.task
    assert "item-742" not in task.task

    assert [
        tool.tool_name
        for tool in task.available_tools
    ] == [
        "create_item",
        "inspect_item",
    ]

    assert task.available_tools[0].parameters == {
        "name": "string",
        "count": "integer",
    }
    assert task.available_tools[1].parameters == {
        "item_id": "string",
    }

    assert len(task.tool_results) == 1
    assert (
        task.tool_results[0].tool_name
        == "create_item"
    )
    assert task.tool_results[0].result == {
        "item_id": "item-742",
    }

    assert task.expected_action is None
    assert task.expected_actions is not None

    assert [
        action.tool_name
        for action in task.expected_actions
    ] == [
        "create_item",
        "inspect_item",
    ]

    assert task.expected_actions[0].arguments == {
        "name": "delta",
        "count": 4,
    }

    # The propagated value must not be encoded
    # as a static expected argument.
    assert task.expected_actions[1].arguments == {}

    assert task.expected_propagations is not None
    assert len(task.expected_propagations) == 1

    propagation = task.expected_propagations[0]

    assert propagation.source_action_index == 0
    assert propagation.source_result_field == "item_id"
    assert propagation.target_action_index == 1
    assert propagation.target_argument == "item_id"

    assert [
        criterion.criterion_id
        for criterion in task.success_criteria
    ] == [
        "tool-calls-observed",
        "tool-sequence-length-match",
        "tool-sequence-order-match",
        "tool-sequence-arguments-match",
        "tool-result-propagated",
    ]

    assert task.enabled is True


def test_canonical_agent_protocol_suite_v0_7():
    suite_bank = SuiteBank(
        Path("benchmark/suites"),
    )

    matches = [
        suite
        for suite in suite_bank.load_all()
        if (
            suite.suite_id == "agent-protocol-core"
            and suite.suite_version == "0.7"
        )
    ]

    assert len(matches) == 1

    suite = matches[0]

    assert suite.family is BenchmarkFamily.AGENT
    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )

    assert suite.task_ids == [
        "agent-protocol-smoke-001",
        "agent-protocol-instruction-001",
        "agent-protocol-structured-output-001",
        "agent-protocol-action-001",
        "agent-protocol-tool-selection-001",
        "agent-protocol-action-sequence-001",
        "agent-protocol-data-flow-001",
    ]

    assert suite.enabled is True
