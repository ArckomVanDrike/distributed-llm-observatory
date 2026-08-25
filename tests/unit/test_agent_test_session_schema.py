from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

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


def make_target() -> TargetManifest:
    return TargetManifest(
        target_id="example-agent",
        display_name="Example Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.FILESYSTEM,
        },
    )


def make_evaluation(
    task_id: str = "agent-filesystem-001",
) -> TaskEvaluation:
    return TaskEvaluation(
        task_id=task_id,
        method=TaskEvaluationMethod.DETERMINISTIC,
        criteria=[
            TaskCriterionEvaluation(
                criterion="file-created",
                passed=True,
                evidence="Expected file exists.",
            ),
            TaskCriterionEvaluation(
                criterion="file-contents-match",
                passed=True,
                evidence="File contents match expected value.",
            ),
        ],
        passed=True,
    )


def make_result() -> AgentTestTaskResult:
    return AgentTestTaskResult(
        task_id="agent-filesystem-001",
        benchmark_version="0.1",
        started_at_utc=NOW,
        finished_at_utc=NOW + timedelta(seconds=2),
        latency_ms=2000,
        task_completed=True,
        retry_count=0,
        human_intervention_count=0,
        metrics={"tool_calls": 1},
        evaluation=make_evaluation(),
    )


def test_agent_test_task_result_is_persistable():
    result = make_result()

    assert result.schema_version == "0.1"
    assert result.task_id == "agent-filesystem-001"
    assert result.task_completed is True
    assert result.evaluation.passed is True
    assert result.metrics["tool_calls"] == 1


def test_task_result_requires_matching_evaluation_task_id():
    with pytest.raises(
        ValidationError,
        match="evaluation task_id",
    ):
        AgentTestTaskResult(
            task_id="agent-filesystem-001",
            benchmark_version="0.1",
            started_at_utc=NOW,
            finished_at_utc=NOW + timedelta(seconds=1),
            latency_ms=1000,
            task_completed=True,
            evaluation=make_evaluation("different-task"),
        )


def test_task_result_rejects_naive_timestamps():
    with pytest.raises(
        ValidationError,
        match="timezone-aware",
    ):
        AgentTestTaskResult(
            task_id="agent-filesystem-001",
            benchmark_version="0.1",
            started_at_utc=NOW.replace(tzinfo=None),
            finished_at_utc=NOW,
            latency_ms=1000,
            task_completed=True,
            evaluation=make_evaluation(),
        )


def test_task_result_rejects_reversed_timestamps():
    with pytest.raises(
        ValidationError,
        match="cannot precede",
    ):
        AgentTestTaskResult(
            task_id="agent-filesystem-001",
            benchmark_version="0.1",
            started_at_utc=NOW,
            finished_at_utc=NOW - timedelta(seconds=1),
            latency_ms=1000,
            task_completed=True,
            evaluation=make_evaluation(),
        )


def test_running_session_can_have_no_results():
    session = AgentTestSession(
        target=make_target(),
        suite_id="agent-core",
        suite_version="0.1",
        status=AgentTestSessionStatus.RUNNING,
        started_at_utc=NOW,
    )

    assert session.schema_version == "0.1"
    assert session.completed_at_utc is None
    assert session.results == []


def test_completed_session_contains_results():
    session = AgentTestSession(
        target=make_target(),
        suite_id="agent-core",
        suite_version="0.1",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=NOW,
        completed_at_utc=NOW + timedelta(seconds=3),
        results=[make_result()],
    )

    assert session.status is AgentTestSessionStatus.COMPLETED
    assert len(session.results) == 1


def test_completed_session_requires_completion_time():
    with pytest.raises(
        ValidationError,
        match="completed_at_utc",
    ):
        AgentTestSession(
            target=make_target(),
            suite_id="agent-core",
            suite_version="0.1",
            status=AgentTestSessionStatus.COMPLETED,
            started_at_utc=NOW,
        )


def test_running_session_rejects_completion_time():
    with pytest.raises(
        ValidationError,
        match="running session",
    ):
        AgentTestSession(
            target=make_target(),
            suite_id="agent-core",
            suite_version="0.1",
            status=AgentTestSessionStatus.RUNNING,
            started_at_utc=NOW,
            completed_at_utc=NOW + timedelta(seconds=1),
        )


def test_session_rejects_reversed_timestamps():
    with pytest.raises(
        ValidationError,
        match="cannot precede",
    ):
        AgentTestSession(
            target=make_target(),
            suite_id="agent-core",
            suite_version="0.1",
            status=AgentTestSessionStatus.COMPLETED,
            started_at_utc=NOW,
            completed_at_utc=NOW - timedelta(seconds=1),
        )


def test_session_records_test_suite_provenance():
    session = AgentTestSession(
        target=make_target(),
        suite_id="agent-core",
        suite_version="0.1",
        status=AgentTestSessionStatus.RUNNING,
        started_at_utc=NOW,
    )

    assert session.suite_id == "agent-core"
    assert session.suite_version == "0.1"


def test_incompatible_selection_requires_reason():
    from pydantic import ValidationError

    from schemas.agent_lab import (
        AgentTestTaskSelection,
        AgentTestTaskSelectionStatus,
    )

    with pytest.raises(
        ValidationError,
        match="missing capabilities or a family mismatch",
    ):
        AgentTestTaskSelection(
            task_id="agent-task-001",
            benchmark_version="0.1",
            status=AgentTestTaskSelectionStatus.INCOMPATIBLE,
        )


def test_selected_selection_rejects_missing_capabilities():
    from pydantic import ValidationError

    from schemas.agent_lab import (
        AgentTestTaskSelection,
        AgentTestTaskSelectionStatus,
    )
    from schemas.target import TargetCapability

    with pytest.raises(
        ValidationError,
        match="Only incompatible task selections",
    ):
        AgentTestTaskSelection(
            task_id="agent-task-001",
            benchmark_version="0.1",
            status=AgentTestTaskSelectionStatus.SELECTED,
            missing_capabilities={
                TargetCapability.FILESYSTEM,
            },
        )


def test_disabled_selection_rejects_family_mismatch():
    from pydantic import ValidationError

    from schemas.agent_lab import (
        AgentTestTaskSelection,
        AgentTestTaskSelectionStatus,
    )

    with pytest.raises(
        ValidationError,
        match="Only incompatible task selections",
    ):
        AgentTestTaskSelection(
            task_id="agent-task-001",
            benchmark_version="0.1",
            status=AgentTestTaskSelectionStatus.DISABLED,
            family_mismatch=True,
        )


def test_session_rejects_duplicate_result_task_ids():
    with pytest.raises(
        ValidationError,
        match="unique task_id",
    ):
        AgentTestSession(
            target=make_target(),
            suite_id="agent-core",
            suite_version="0.1",
            status=AgentTestSessionStatus.COMPLETED,
            started_at_utc=NOW,
            completed_at_utc=NOW + timedelta(seconds=3),
            results=[
                make_result(),
                make_result(),
            ],
        )
