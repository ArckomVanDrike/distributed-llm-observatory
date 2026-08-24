from datetime import datetime, timedelta, timezone

from observer.core.agent_technical_report import (
    build_agent_technical_report,
)
from schemas.agent_lab import (
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

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


def make_evaluation(
    task_id: str,
    *,
    passed: bool,
) -> TaskEvaluation:
    return TaskEvaluation(
        task_id=task_id,
        method=TaskEvaluationMethod.DETERMINISTIC,
        criteria=[
            TaskCriterionEvaluation(
                criterion="criterion-1",
                passed=passed,
            ),
        ],
        passed=passed,
    )


def make_result(
    task_id: str,
    *,
    latency_ms: float,
    completed: bool,
    passed: bool,
    retries: int = 0,
    interventions: int = 0,
) -> AgentTestTaskResult:
    return AgentTestTaskResult(
        task_id=task_id,
        benchmark_version="0.1",
        started_at_utc=NOW,
        finished_at_utc=NOW + timedelta(
            milliseconds=latency_ms,
        ),
        latency_ms=latency_ms,
        task_completed=completed,
        retry_count=retries,
        human_intervention_count=interventions,
        evaluation=make_evaluation(
            task_id,
            passed=passed,
        ),
    )


def make_session(
    results: list[AgentTestTaskResult],
) -> AgentTestSession:
    return AgentTestSession(
        target=TargetManifest(
            target_id="example-agent",
            display_name="Example Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id="agent-core",
        suite_version="0.1",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=NOW,
        completed_at_utc=NOW + timedelta(seconds=10),
        results=results,
    )


def test_report_is_derived_from_session_results():
    session = make_session(
        [
            make_result(
                "task-1",
                latency_ms=1000,
                completed=True,
                passed=True,
            ),
            make_result(
                "task-2",
                latency_ms=2000,
                completed=True,
                passed=False,
                retries=2,
                interventions=1,
            ),
            make_result(
                "task-3",
                latency_ms=3000,
                completed=False,
                passed=False,
                retries=1,
            ),
        ],
    )

    report = build_agent_technical_report(
        session,
        generated_at_utc=NOW + timedelta(seconds=20),
    )

    assert report.session_id == session.session_id
    assert report.target_id == "example-agent"
    assert report.suite_id == "agent-core"
    assert report.suite_version == "0.1"

    assert report.total_tasks == 3
    assert report.passed_tasks == 1
    assert report.failed_tasks == 2

    assert report.task_completion_rate == 2 / 3
    assert report.pass_rate == 1 / 3

    assert report.median_latency_ms == 2000
    assert report.total_retries == 3
    assert report.total_human_interventions == 1


def test_empty_session_produces_empty_report():
    session = make_session([])

    report = build_agent_technical_report(
        session,
        generated_at_utc=NOW + timedelta(seconds=20),
    )

    assert report.total_tasks == 0
    assert report.passed_tasks == 0
    assert report.failed_tasks == 0
    assert report.task_completion_rate == 0.0
    assert report.pass_rate is None
    assert report.median_latency_ms is None


def test_builder_emits_traceable_findings():
    session = make_session(
        [
            make_result(
                "task-1",
                latency_ms=1000,
                completed=True,
                passed=True,
            ),
            make_result(
                "task-2",
                latency_ms=2000,
                completed=True,
                passed=False,
            ),
        ],
    )

    report = build_agent_technical_report(
        session,
        generated_at_utc=NOW + timedelta(seconds=20),
    )

    assert report.findings
    assert any(
        "1 of 2" in finding
        for finding in report.findings
    )
