from pathlib import Path

from observer.core.suite_bank import SuiteBank
from observer.core.task_bank import TaskBank
from schemas.benchmark import BenchmarkHarnessProfile


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
    assert suite.enabled is True
