from pathlib import Path

from observer.core.suite_bank import SuiteBank
from observer.core.suite_registry import SuiteRegistry
from observer.core.task_bank import TaskBank

PROTOCOL_SUITE_VERSIONS = (
    "0.1",
    "0.2",
    "0.3",
    "0.4",
    "0.5",
    "0.6",
    "0.7",
    "0.8",
    "0.9",
    "0.10",
    "1.0",
)


def build_registry() -> SuiteRegistry:
    return SuiteRegistry(
        suite_bank=SuiteBank(
            Path("benchmark/suites"),
        ),
        task_bank=TaskBank(
            Path("benchmark/tasks"),
        ),
    )


def test_all_published_protocol_versions_remain_exactly_resolvable():
    registry = build_registry()

    for version in PROTOCOL_SUITE_VERSIONS:
        resolved = registry.resolve(
            suite_id="agent-protocol-core",
            suite_version=version,
        )

        assert (
            resolved.suite.suite_id
            == "agent-protocol-core"
        )
        assert resolved.suite.suite_version == version
        assert resolved.tasks

        assert [
            task.task_id
            for task in resolved.tasks
        ] == resolved.suite.task_ids


def test_protocol_core_has_exactly_one_active_suite():
    suites = [
        suite
        for suite in SuiteBank(
            Path("benchmark/suites"),
        ).load_all()
        if suite.suite_id == "agent-protocol-core"
    ]

    assert {
        suite.suite_version
        for suite in suites
    } == set(PROTOCOL_SUITE_VERSIONS)

    active = [
        suite
        for suite in suites
        if suite.enabled
    ]

    assert len(active) == 1
    assert active[0].suite_version == "1.0"


def test_protocol_suite_history_is_monotonic():
    registry = build_registry()

    previous_task_ids: list[str] = []

    for version in PROTOCOL_SUITE_VERSIONS:
        resolved = registry.resolve(
            suite_id="agent-protocol-core",
            suite_version=version,
        )

        current_task_ids = [
            task.task_id
            for task in resolved.tasks
        ]

        assert current_task_ids[
            : len(previous_task_ids)
        ] == previous_task_ids

        assert len(current_task_ids) >= len(
            previous_task_ids
        )

        previous_task_ids = current_task_ids



def test_protocol_v1_freezes_v0_10_behavior():
    registry = build_registry()

    v0_10 = registry.resolve(
        suite_id="agent-protocol-core",
        suite_version="0.10",
    )
    v1_0 = registry.resolve(
        suite_id="agent-protocol-core",
        suite_version="1.0",
    )

    assert (
        v1_0.suite.family
        is v0_10.suite.family
    )
    assert (
        v1_0.suite.harness_profile
        is v0_10.suite.harness_profile
    )

    assert (
        v1_0.suite.task_ids
        == v0_10.suite.task_ids
    )

    assert [
        task.task_id
        for task in v1_0.tasks
    ] == [
        task.task_id
        for task in v0_10.tasks
    ]

    assert v0_10.suite.enabled is False
    assert v1_0.suite.enabled is True
