import pytest
from pydantic import ValidationError

from schemas.benchmark import (
    BenchmarkFamily,
    BenchmarkHarnessProfile,
    BenchmarkSuite,
)


def test_shared_workspace_suite_declares_harness_profile():
    suite = BenchmarkSuite(
        suite_id="agent-core",
        suite_version="0.1",
        family=BenchmarkFamily.AGENT,
        harness_profile=BenchmarkHarnessProfile.SHARED_WORKSPACE,
        task_ids=[
            "agent-filesystem-001",
        ],
    )

    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SHARED_WORKSPACE
    )


def test_sut_protocol_suite_declares_harness_profile():
    suite = BenchmarkSuite(
        suite_id="agent-protocol-core",
        suite_version="0.1",
        family=BenchmarkFamily.AGENT,
        harness_profile=BenchmarkHarnessProfile.SUT_PROTOCOL,
        task_ids=[
            "agent-protocol-smoke-001",
        ],
    )

    assert (
        suite.harness_profile
        is BenchmarkHarnessProfile.SUT_PROTOCOL
    )


def test_benchmark_suite_requires_explicit_harness_profile():
    with pytest.raises(ValidationError):
        BenchmarkSuite(
            suite_id="agent-core",
            suite_version="0.1",
            family=BenchmarkFamily.AGENT,
            task_ids=[
                "agent-filesystem-001",
            ],
        )


def test_benchmark_suite_rejects_unknown_harness_profile():
    with pytest.raises(ValidationError):
        BenchmarkSuite(
            suite_id="agent-core",
            suite_version="0.1",
            family=BenchmarkFamily.AGENT,
            harness_profile="magic_remote_filesystem",
            task_ids=[
                "agent-filesystem-001",
            ],
        )
