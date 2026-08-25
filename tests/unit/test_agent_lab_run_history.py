from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from observer.core.agent_lab_artifact_io import (
    write_agent_lab_run_artifact,
)
from observer.core.agent_lab_run_history import (
    AgentLabRunHistory,
)
from schemas.agent_lab import (
    AgentLabRunArtifact,
    AgentTechnicalReport,
    AgentTestSession,
    AgentTestSessionStatus,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


def build_artifact(
    *,
    target_id: str,
    started_at_utc: datetime,
    session_id: UUID,
) -> AgentLabRunArtifact:
    session = AgentTestSession(
        session_id=session_id,
        target=TargetManifest(
            target_id=target_id,
            display_name=target_id,
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id="agent-protocol-core",
        suite_version="1.0",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=started_at_utc,
        completed_at_utc=started_at_utc,
    )

    report = AgentTechnicalReport(
        session_id=session.session_id,
        target_id=session.target.target_id,
        suite_id=session.suite_id,
        suite_version=session.suite_version,
        generated_at_utc=started_at_utc,
        total_tasks=0,
        passed_tasks=0,
        failed_tasks=0,
        task_completion_rate=0.0,
        pass_rate=None,
        median_latency_ms=None,
    )

    return AgentLabRunArtifact(
        session=session,
        technical_report=report,
    )


def test_history_loads_artifacts_in_deterministic_chronological_order(
    tmp_path: Path,
):
    same_time = datetime(
        2026,
        8,
        25,
        18,
        0,
        tzinfo=timezone.utc,
    )
    later_time = datetime(
        2026,
        8,
        25,
        19,
        0,
        tzinfo=timezone.utc,
    )

    first = build_artifact(
        target_id="agent-one",
        started_at_utc=same_time,
        session_id=UUID(
            "00000000-0000-0000-0000-000000000001"
        ),
    )
    second = build_artifact(
        target_id="agent-two",
        started_at_utc=same_time,
        session_id=UUID(
            "00000000-0000-0000-0000-000000000002"
        ),
    )
    third = build_artifact(
        target_id="agent-one",
        started_at_utc=later_time,
        session_id=UUID(
            "00000000-0000-0000-0000-000000000003"
        ),
    )

    nested = tmp_path / "nested"
    nested.mkdir()

    write_agent_lab_run_artifact(
        third,
        tmp_path / "z.json",
    )
    write_agent_lab_run_artifact(
        second,
        nested / "a.json",
    )
    write_agent_lab_run_artifact(
        first,
        tmp_path / "m.json",
    )

    history = AgentLabRunHistory(
        tmp_path,
    )

    artifacts = history.load_all()

    assert [
        artifact.session.session_id
        for artifact in artifacts
    ] == [
        first.session.session_id,
        second.session.session_id,
        third.session.session_id,
    ]


def test_history_filters_runs_by_target(
    tmp_path: Path,
):
    earlier = datetime(
        2026,
        8,
        25,
        18,
        0,
        tzinfo=timezone.utc,
    )
    later = datetime(
        2026,
        8,
        25,
        19,
        0,
        tzinfo=timezone.utc,
    )

    first = build_artifact(
        target_id="agent-one",
        started_at_utc=earlier,
        session_id=UUID(
            "00000000-0000-0000-0000-000000000011"
        ),
    )
    other = build_artifact(
        target_id="agent-two",
        started_at_utc=earlier,
        session_id=UUID(
            "00000000-0000-0000-0000-000000000012"
        ),
    )
    second = build_artifact(
        target_id="agent-one",
        started_at_utc=later,
        session_id=UUID(
            "00000000-0000-0000-0000-000000000013"
        ),
    )

    write_agent_lab_run_artifact(
        second,
        tmp_path / "second.json",
    )
    write_agent_lab_run_artifact(
        other,
        tmp_path / "other.json",
    )
    write_agent_lab_run_artifact(
        first,
        tmp_path / "first.json",
    )

    history = AgentLabRunHistory(
        tmp_path,
    )

    artifacts = history.for_target(
        "agent-one",
    )

    assert [
        artifact.session.session_id
        for artifact in artifacts
    ] == [
        first.session.session_id,
        second.session.session_id,
    ]


def test_history_rejects_duplicate_session_ids(
    tmp_path: Path,
):
    shared_session_id = (
        "00000000-0000-0000-0000-000000000099"
    )

    first = build_artifact(
        session_id=shared_session_id,
        target_id="duplicate-session-agent",
        started_at_utc=datetime(
            2026,
            8,
            24,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )
    second = build_artifact(
        session_id=shared_session_id,
        target_id="duplicate-session-agent",
        started_at_utc=datetime(
            2026,
            8,
            25,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    write_agent_lab_run_artifact(
        first,
        tmp_path / "first.json",
    )
    write_agent_lab_run_artifact(
        second,
        tmp_path / "second.json",
    )

    history = AgentLabRunHistory(tmp_path)

    with pytest.raises(
        ValueError,
        match="duplicate session_id",
    ):
        history.load_all()
