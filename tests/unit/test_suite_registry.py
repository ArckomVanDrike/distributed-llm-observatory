import json
from pathlib import Path

import pytest

from observer.core.suite_bank import SuiteBank
from observer.core.suite_registry import (
    SuiteRegistry,
    SuiteRegistryError,
)
from observer.core.task_bank import TaskBank
from schemas.benchmark import (
    BenchmarkFamily,
    BenchmarkHarnessProfile,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


def test_resolves_canonical_agent_suite():
    registry = SuiteRegistry(
        suite_bank=SuiteBank(
            Path("benchmark/suites"),
        ),
        task_bank=TaskBank(
            Path("benchmark/tasks"),
        ),
    )

    resolved = registry.resolve(
        suite_id="agent-core",
        suite_version="0.1",
    )

    assert resolved.suite.suite_id == "agent-core"
    assert resolved.suite.suite_version == "0.1"
    assert resolved.suite.family is BenchmarkFamily.AGENT

    assert [
        task.task_id
        for task in resolved.tasks
    ] == [
        "agent-filesystem-001",
    ]


def test_registry_rejects_unknown_suite():
    registry = SuiteRegistry(
        suite_bank=SuiteBank(
            Path("benchmark/suites"),
        ),
        task_bank=TaskBank(
            Path("benchmark/tasks"),
        ),
    )

    with pytest.raises(
        SuiteRegistryError,
        match="Benchmark suite not found",
    ):
        registry.resolve(
            suite_id="missing-suite",
            suite_version="0.1",
        )


def test_registry_rejects_missing_referenced_task(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    (suite_root / "suite.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-test",
                "suite_version": "0.1",
                "family": "agent",
                "harness_profile": "shared_workspace",
                "task_ids": [
                    "missing-task-001",
                ],
            }
        ),
        encoding="utf-8",
    )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    with pytest.raises(
        SuiteRegistryError,
        match="missing-task-001",
    ):
        registry.resolve(
            suite_id="agent-test",
            suite_version="0.1",
        )


def test_registry_rejects_task_family_mismatch(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    (suite_root / "suite.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-test",
                "suite_version": "0.1",
                "family": "agent",
                "harness_profile": "shared_workspace",
                "task_ids": [
                    "system-task-001",
                ],
            }
        ),
        encoding="utf-8",
    )

    (task_root / "task.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "task_id": "system-task-001",
                "benchmark_version": "0.1",
                "evaluator_id": "test-evaluator-v0-1",
                "family": "ai_system",
                "category": "technical",
                "difficulty": "easy",
                "task": "Complete the system task.",
                "required_capabilities": [
                    "text"
                ],
                "success_criteria": [
                    {
                        "criterion_id": "completed",
                        "description": "The task is complete."
                    }
                ],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    with pytest.raises(
        SuiteRegistryError,
        match="family",
    ):
        registry.resolve(
            suite_id="agent-test",
            suite_version="0.1",
        )


def test_registry_preserves_suite_task_order(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    task_ids = [
        "agent-task-second",
        "agent-task-first",
    ]

    (suite_root / "suite.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-order",
                "suite_version": "0.1",
                "family": "agent",
                "harness_profile": "shared_workspace",
                "task_ids": task_ids,
            }
        ),
        encoding="utf-8",
    )

    for task_id in reversed(task_ids):
        (task_root / f"{task_id}.json").write_text(
            json.dumps(
                {
                    "schema_version": "0.1",
                    "task_id": task_id,
                    "benchmark_version": "0.1",
                    "evaluator_id": "test-evaluator-v0-1",
                    "family": "agent",
                    "category": "technical",
                    "difficulty": "easy",
                    "task": "Complete the task.",
                    "required_capabilities": [
                        "text"
                    ],
                    "success_criteria": [
                        {
                            "criterion_id": "completed",
                            "description": "The task is complete."
                        }
                    ],
                    "enabled": True,
                }
            ),
            encoding="utf-8",
        )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    resolved = registry.resolve(
        suite_id="agent-order",
        suite_version="0.1",
    )

    assert [
        task.task_id
        for task in resolved.tasks
    ] == task_ids


def test_registry_returns_enabled_suites_for_target_family(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    suites = [
        {
            "schema_version": "0.1",
            "suite_id": "agent-core",
            "suite_version": "0.1",
            "family": "agent",
            "harness_profile": "shared_workspace",
            "task_ids": [
                "agent-task-001",
            ],
            "enabled": True,
        },
        {
            "schema_version": "0.1",
            "suite_id": "system-core",
            "suite_version": "0.1",
            "family": "ai_system",
            "harness_profile": "shared_workspace",
            "task_ids": [
                "system-task-001",
            ],
            "enabled": True,
        },
        {
            "schema_version": "0.1",
            "suite_id": "agent-disabled",
            "suite_version": "0.1",
            "family": "agent",
            "harness_profile": "shared_workspace",
            "task_ids": [
                "agent-task-002",
            ],
            "enabled": False,
        },
    ]

    for index, payload in enumerate(suites):
        (suite_root / f"suite-{index}.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    candidates = registry.candidates_for_target(
        target,
    )

    assert [
        (
            suite.suite_id,
            suite.suite_version,
        )
        for suite in candidates
    ] == [
        (
            "agent-core",
            "0.1",
        ),
    ]


def test_registry_returns_all_enabled_versions_for_target(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    for version in [
        "0.1",
        "0.2",
    ]:
        (suite_root / f"agent-core-{version}.json").write_text(
            json.dumps(
                {
                    "schema_version": "0.1",
                    "suite_id": "agent-core",
                    "suite_version": version,
                    "family": "agent",
                    "harness_profile": "shared_workspace",
                    "task_ids": [
                        "agent-task-001",
                    ],
                    "enabled": True,
                }
            ),
            encoding="utf-8",
        )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    candidates = registry.candidates_for_target(
        target,
    )

    assert {
        (
            suite.suite_id,
            suite.suite_version,
        )
        for suite in candidates
    } == {
        (
            "agent-core",
            "0.1",
        ),
        (
            "agent-core",
            "0.2",
        ),
    }


def test_registry_returns_no_candidates_for_unmatched_family(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    (suite_root / "agent.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-core",
                "suite_version": "0.1",
                "family": "agent",
                "harness_profile": "shared_workspace",
                "task_ids": [
                    "agent-task-001",
                ],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-system",
        display_name="Example System",
        target_type=TargetType.AI_SYSTEM,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    assert registry.candidates_for_target(
        target,
    ) == []


def test_registry_resolves_unique_suite_for_target(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    (suite_root / "suite.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-core",
                "suite_version": "0.1",
                "family": "agent",
                "harness_profile": "shared_workspace",
                "task_ids": [
                    "agent-task-001",
                ],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    (task_root / "task.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "task_id": "agent-task-001",
                "benchmark_version": "0.1",
                "evaluator_id": "test-evaluator-v0-1",
                "family": "agent",
                "category": "technical",
                "difficulty": "easy",
                "task": "Complete the task.",
                "required_capabilities": [
                    "text"
                ],
                "success_criteria": [
                    {
                        "criterion_id": "completed",
                        "description": "The task is complete."
                    }
                ],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    resolved = registry.resolve_unique_for_target(
        target,
        harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
    )

    assert resolved.suite.suite_id == "agent-core"
    assert resolved.suite.suite_version == "0.1"
    assert [
        task.task_id
        for task in resolved.tasks
    ] == [
        "agent-task-001",
    ]


def test_registry_rejects_no_suite_for_target(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    with pytest.raises(
        SuiteRegistryError,
        match="No enabled benchmark suite",
    ):
        registry.resolve_unique_for_target(
            target,
            harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
        )


def test_registry_rejects_ambiguous_suites_for_target(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    for version in [
        "0.1",
        "0.2",
    ]:
        (suite_root / f"suite-{version}.json").write_text(
            json.dumps(
                {
                    "schema_version": "0.1",
                    "suite_id": "agent-core",
                    "suite_version": version,
                    "family": "agent",
                    "harness_profile": "shared_workspace",
                    "task_ids": [
                        "agent-task-001",
                    ],
                    "enabled": True,
                }
            ),
            encoding="utf-8",
        )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    with pytest.raises(
        SuiteRegistryError,
        match="Multiple enabled benchmark suites",
    ):
        registry.resolve_unique_for_target(
            target,
            harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
        )


def test_registry_filters_candidates_by_harness_profile(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    suites = [
        {
            "schema_version": "0.1",
            "suite_id": "agent-workspace",
            "suite_version": "0.1",
            "family": "agent",
            "harness_profile": "shared_workspace",
            "task_ids": [
                "agent-workspace-001",
            ],
            "enabled": True,
        },
        {
            "schema_version": "0.1",
            "suite_id": "agent-protocol",
            "suite_version": "0.1",
            "family": "agent",
            "harness_profile": "sut_protocol",
            "task_ids": [
                "agent-protocol-001",
            ],
            "enabled": True,
        },
    ]

    for index, payload in enumerate(suites):
        (suite_root / f"suite-{index}.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    candidates = registry.candidates_for_target(
        target,
        harness_profile=BenchmarkHarnessProfile.SUT_PROTOCOL,
    )

    assert [
        (
            suite.suite_id,
            suite.suite_version,
        )
        for suite in candidates
    ] == [
        (
            "agent-protocol",
            "0.1",
        ),
    ]


def test_registry_returns_no_candidates_for_unmatched_harness_profile(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    (suite_root / "suite.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "suite_id": "agent-workspace",
                "suite_version": "0.1",
                "family": "agent",
                "harness_profile": "shared_workspace",
                "task_ids": [
                    "agent-workspace-001",
                ],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    assert registry.candidates_for_target(
        target,
        harness_profile=BenchmarkHarnessProfile.SUT_PROTOCOL,
    ) == []


def test_resolve_unique_for_target_uses_harness_profile(
    tmp_path: Path,
):
    suite_root = tmp_path / "suites"
    task_root = tmp_path / "tasks"

    suite_root.mkdir()
    task_root.mkdir()

    suites = [
        {
            "schema_version": "0.1",
            "suite_id": "agent-workspace",
            "suite_version": "0.1",
            "family": "agent",
            "harness_profile": "shared_workspace",
            "task_ids": [
                "agent-workspace-001",
            ],
            "enabled": True,
        },
        {
            "schema_version": "0.1",
            "suite_id": "agent-protocol",
            "suite_version": "0.1",
            "family": "agent",
            "harness_profile": "sut_protocol",
            "task_ids": [
                "agent-protocol-001",
            ],
            "enabled": True,
        },
    ]

    for index, payload in enumerate(suites):
        (suite_root / f"suite-{index}.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    (task_root / "agent-protocol-001.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "task_id": "agent-protocol-001",
                "benchmark_version": "0.1",
                "evaluator_id": "test-evaluator-v0-1",
                "family": "agent",
                "category": "technical",
                "difficulty": "easy",
                "task": "Complete the protocol task.",
                "required_capabilities": [
                    "text"
                ],
                "success_criteria": [
                    {
                        "criterion_id": "completed",
                        "description": "The task is complete."
                    }
                ],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    registry = SuiteRegistry(
        suite_bank=SuiteBank(suite_root),
        task_bank=TaskBank(task_root),
    )

    target = TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    resolved = registry.resolve_unique_for_target(
        target,
        harness_profile=BenchmarkHarnessProfile.SUT_PROTOCOL,
    )

    assert resolved.suite.suite_id == "agent-protocol"
    assert (
        resolved.suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )
    assert [
        task.task_id
        for task in resolved.tasks
    ] == [
        "agent-protocol-001",
    ]
