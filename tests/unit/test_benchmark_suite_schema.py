import pytest
from pydantic import ValidationError

from schemas.benchmark import (
    BenchmarkFamily,
    BenchmarkHarnessProfile,
    BenchmarkSuite,
)


def test_agent_benchmark_suite():
    suite = BenchmarkSuite(
        suite_id="agent-core",
        suite_version="0.1",
        family=BenchmarkFamily.AGENT,
        harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
        task_ids=[
            "agent-filesystem-001",
        ],
    )

    assert suite.schema_version == "0.1"
    assert suite.suite_id == "agent-core"
    assert suite.suite_version == "0.1"
    assert suite.family is BenchmarkFamily.AGENT
    assert suite.task_ids == [
        "agent-filesystem-001",
    ]
    assert suite.enabled is True


def test_ai_system_benchmark_suite():
    suite = BenchmarkSuite(
        suite_id="ai-system-core",
        suite_version="0.1",
        family=BenchmarkFamily.AI_SYSTEM,
        harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
        task_ids=[
            "memory-recall-001",
        ],
    )

    assert suite.family is BenchmarkFamily.AI_SYSTEM


def test_benchmark_suite_rejects_foundation_model_family():
    with pytest.raises(
        ValidationError,
        match="BenchmarkSuite",
    ):
        BenchmarkSuite(
            suite_id="foundation-core",
            suite_version="0.1",
            family=BenchmarkFamily.FOUNDATION_MODEL,
            harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
            task_ids=[
                "reasoning-task-001",
            ],
        )


def test_benchmark_suite_requires_task_ids():
    with pytest.raises(ValidationError):
        BenchmarkSuite(
            suite_id="agent-core",
            suite_version="0.1",
            family=BenchmarkFamily.AGENT,
            harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
            task_ids=[],
        )


def test_benchmark_suite_rejects_duplicate_task_ids():
    with pytest.raises(
        ValidationError,
        match="unique",
    ):
        BenchmarkSuite(
            suite_id="agent-core",
            suite_version="0.1",
            family=BenchmarkFamily.AGENT,
            harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
            task_ids=[
                "agent-filesystem-001",
                "agent-filesystem-001",
            ],
        )


def test_benchmark_suite_task_ids_use_stable_slug_format():
    with pytest.raises(ValidationError):
        BenchmarkSuite(
            suite_id="agent-core",
            suite_version="0.1",
            family=BenchmarkFamily.AGENT,
            harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
            task_ids=[
                "Bad Task ID",
            ],
        )


def test_benchmark_suite_id_uses_stable_slug_format():
    with pytest.raises(ValidationError):
        BenchmarkSuite(
            suite_id="Bad Suite ID",
            suite_version="0.1",
            family=BenchmarkFamily.AGENT,
            harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
            task_ids=[
                "agent-filesystem-001",
            ],
        )
