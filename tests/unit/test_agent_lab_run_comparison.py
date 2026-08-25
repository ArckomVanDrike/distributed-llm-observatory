from datetime import datetime, timezone
from uuid import UUID

import pytest

from observer.core.agent_lab_run_comparison import (
    AgentTaskOutcomeTransition,
    compare_agent_lab_runs,
)
from schemas.agent_lab import (
    AgentLabRunArtifact,
    AgentTechnicalReport,
    AgentTestSession,
    AgentTestSessionStatus,
    AgentTestTaskResult,
)
from schemas.evaluation import (
    TaskCriterionEvaluation,
    TaskEvaluation,
    TaskEvaluationMethod,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)

NOW = datetime(
    2026,
    8,
    25,
    18,
    0,
    tzinfo=timezone.utc,
)


def build_task_result(
    task_id: str,
    *,
    passed: bool = True,
    latency_ms: float = 100.0,
    retry_count: int = 0,
    human_intervention_count: int = 0,
) -> AgentTestTaskResult:
    return AgentTestTaskResult(
        task_id=task_id,
        benchmark_version="0.1",
        started_at_utc=NOW,
        finished_at_utc=NOW,
        latency_ms=latency_ms,
        task_completed=passed,
        retry_count=retry_count,
        human_intervention_count=(
            human_intervention_count
        ),
        evaluation=TaskEvaluation(
            task_id=task_id,
            method=TaskEvaluationMethod.DETERMINISTIC,
            criteria=[
                TaskCriterionEvaluation(
                    criterion="criterion-1",
                    passed=passed,
                ),
            ],
            passed=passed,
        ),
    )


def build_artifact(
    *,
    session_id: str,
    target_id: str = "comparison-agent",
    suite_id: str = "agent-protocol-core",
    suite_version: str = "1.0",
    task_ids: tuple[str, ...] = (
        "agent-protocol-smoke-001",
    ),
    task_passed: dict[str, bool] | None = None,
    latency_ms: float = 100.0,
    retry_count: int = 0,
    human_intervention_count: int = 0,
) -> AgentLabRunArtifact:
    task_passed = task_passed or {}

    results = [
        build_task_result(
            task_id,
            passed=task_passed.get(
                task_id,
                True,
            ),
            latency_ms=latency_ms,
            retry_count=retry_count,
            human_intervention_count=(
                human_intervention_count
            ),
        )
        for task_id in task_ids
    ]

    session = AgentTestSession(
        session_id=UUID(session_id),
        target=TargetManifest(
            target_id=target_id,
            display_name=target_id,
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id=suite_id,
        suite_version=suite_version,
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=NOW,
        completed_at_utc=NOW,
        results=results,
    )

    report = AgentTechnicalReport(
        session_id=session.session_id,
        target_id=target_id,
        suite_id=suite_id,
        suite_version=suite_version,
        generated_at_utc=NOW,
        total_tasks=len(results),
        passed_tasks=sum(
            result.evaluation.passed
            for result in results
        ),
        failed_tasks=sum(
            not result.evaluation.passed
            for result in results
        ),
        task_completion_rate=(
            sum(
                result.task_completed
                for result in results
            )
            / len(results)
            if results
            else 0.0
        ),
        pass_rate=(
            sum(
                result.evaluation.passed
                for result in results
            )
            / len(results)
            if results
            else None
        ),
        median_latency_ms=100.0 if results else None,
    )

    return AgentLabRunArtifact(
        session=session,
        technical_report=report,
    )


def test_comparison_rejects_different_targets():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000001"
        ),
        target_id="agent-one",
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000002"
        ),
        target_id="agent-two",
    )

    with pytest.raises(
        ValueError,
        match="different targets",
    ):
        compare_agent_lab_runs(
            candidate,
            baseline,
        )


def test_comparison_rejects_different_suites():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000003"
        ),
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000004"
        ),
        suite_id="other-suite",
    )

    with pytest.raises(
        ValueError,
        match="different suites",
    ):
        compare_agent_lab_runs(
            candidate,
            baseline,
        )


def test_comparison_rejects_different_suite_versions():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000005"
        ),
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000006"
        ),
        suite_version="1.1",
    )

    with pytest.raises(
        ValueError,
        match="different suite versions",
    ):
        compare_agent_lab_runs(
            candidate,
            baseline,
        )


def test_comparison_rejects_different_task_coverage():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000007"
        ),
        task_ids=(
            "agent-protocol-smoke-001",
            "agent-protocol-instruction-001",
        ),
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000008"
        ),
        task_ids=(
            "agent-protocol-smoke-001",
        ),
    )

    with pytest.raises(
        ValueError,
        match="different task coverage",
    ):
        compare_agent_lab_runs(
            candidate,
            baseline,
        )


def test_comparison_rejects_same_session():
    artifact = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000009"
        ),
    )

    with pytest.raises(
        ValueError,
        match="same session",
    ):
        compare_agent_lab_runs(
            artifact,
            artifact,
        )



def test_comparison_reports_per_task_outcome_transitions():
    task_ids = (
        "task-unchanged-pass",
        "task-pass-to-fail",
        "task-fail-to-pass",
        "task-unchanged-fail",
    )

    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000021"
        ),
        task_ids=task_ids,
        task_passed={
            "task-unchanged-pass": True,
            "task-pass-to-fail": True,
            "task-fail-to-pass": False,
            "task-unchanged-fail": False,
        },
    )

    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000022"
        ),
        task_ids=task_ids,
        task_passed={
            "task-unchanged-pass": True,
            "task-pass-to-fail": False,
            "task-fail-to-pass": True,
            "task-unchanged-fail": False,
        },
    )

    comparison = compare_agent_lab_runs(
        candidate,
        baseline,
    )

    assert (
        comparison.baseline_session_id
        == baseline.session.session_id
    )
    assert (
        comparison.candidate_session_id
        == candidate.session.session_id
    )

    assert [
        (
            change.task_id,
            change.baseline_passed,
            change.candidate_passed,
            change.transition,
        )
        for change in comparison.task_changes
    ] == [
        (
            "task-fail-to-pass",
            False,
            True,
            AgentTaskOutcomeTransition.FAIL_TO_PASS,
        ),
        (
            "task-pass-to-fail",
            True,
            False,
            AgentTaskOutcomeTransition.PASS_TO_FAIL,
        ),
        (
            "task-unchanged-fail",
            False,
            False,
            AgentTaskOutcomeTransition.UNCHANGED_FAIL,
        ),
        (
            "task-unchanged-pass",
            True,
            True,
            AgentTaskOutcomeTransition.UNCHANGED_PASS,
        ),
    ]


def test_comparison_summarizes_task_outcome_changes():
    task_ids = (
        "task-unchanged-pass",
        "task-pass-to-fail",
        "task-fail-to-pass",
        "task-unchanged-fail",
    )

    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000031"
        ),
        task_ids=task_ids,
        task_passed={
            "task-unchanged-pass": True,
            "task-pass-to-fail": True,
            "task-fail-to-pass": False,
            "task-unchanged-fail": False,
        },
    )

    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000032"
        ),
        task_ids=task_ids,
        task_passed={
            "task-unchanged-pass": True,
            "task-pass-to-fail": False,
            "task-fail-to-pass": True,
            "task-unchanged-fail": False,
        },
    )

    comparison = compare_agent_lab_runs(
        candidate,
        baseline,
    )

    assert comparison.regressions == 1
    assert comparison.improvements == 1
    assert comparison.unchanged == 2
    assert comparison.total_tasks == 4



def test_comparison_reports_observed_metric_deltas():
    task_ids = (
        "agent-protocol-smoke-001",
    )

    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000041"
        ),
        task_ids=task_ids,
        task_passed={
            "agent-protocol-smoke-001": False,
        },
        latency_ms=100.0,
        retry_count=2,
        human_intervention_count=1,
    )

    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000042"
        ),
        task_ids=task_ids,
        task_passed={
            "agent-protocol-smoke-001": True,
        },
        latency_ms=250.0,
        retry_count=1,
        human_intervention_count=3,
    )

    comparison = compare_agent_lab_runs(
        candidate,
        baseline,
    )

    assert comparison.pass_rate_delta == 1.0
    assert comparison.median_latency_ms_delta == 150.0
    assert comparison.retry_delta == -1
    assert comparison.human_intervention_delta == 2


def test_comparison_handles_empty_compatible_runs():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000051"
        ),
        task_ids=(),
    )

    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000052"
        ),
        task_ids=(),
    )

    comparison = compare_agent_lab_runs(
        candidate,
        baseline,
    )

    assert comparison.total_tasks == 0
    assert comparison.regressions == 0
    assert comparison.improvements == 0
    assert comparison.unchanged == 0

    assert comparison.pass_rate_delta is None
    assert comparison.median_latency_ms_delta is None

    assert comparison.retry_delta == 0
    assert comparison.human_intervention_delta == 0
