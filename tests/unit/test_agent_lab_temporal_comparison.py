from datetime import datetime, timezone
from uuid import UUID

import pytest

from observer.core.agent_lab_temporal_comparison import (
    compare_temporal_agent_observations,
)
from observer.core.agent_technical_report import (
    build_agent_technical_report,
)
from schemas.agent_lab import (
    AgentLabRunArtifact,
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
    session_id: str,
    started_at_utc: datetime,
    observer_id: str | None = "observer-test",
    region_code: str | None = "CL-Los-Lagos",
) -> AgentLabRunArtifact:
    session = AgentTestSession(
        session_id=UUID(session_id),
        observer_id=observer_id,
        region_code=region_code,
        target=TargetManifest(
            target_id="temporal-agent",
            display_name="Temporal Agent",
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

    report = build_agent_technical_report(
        session,
        generated_at_utc=started_at_utc,
    )

    return AgentLabRunArtifact(
        session=session,
        technical_report=report,
    )


def test_temporal_comparison_preserves_observation_context():
    baseline_time = datetime(
        2026,
        8,
        24,
        20,
        0,
        tzinfo=timezone.utc,
    )
    candidate_time = datetime(
        2026,
        8,
        25,
        20,
        0,
        tzinfo=timezone.utc,
    )

    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000061"
        ),
        started_at_utc=baseline_time,
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000062"
        ),
        started_at_utc=candidate_time,
    )

    result = compare_temporal_agent_observations(
        candidate,
        baseline,
    )

    assert result.observer_id == "observer-test"
    assert result.region_code == "CL-Los-Lagos"
    assert result.baseline_started_at_utc == baseline_time
    assert result.candidate_started_at_utc == candidate_time

    assert result.run_comparison.total_tasks == 0
    assert result.run_comparison.regressions == 0
    assert result.run_comparison.improvements == 0


def test_temporal_comparison_rejects_incomplete_provenance():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000071"
        ),
        started_at_utc=datetime(
            2026,
            8,
            24,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000072"
        ),
        started_at_utc=datetime(
            2026,
            8,
            25,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        observer_id=None,
    )

    with pytest.raises(
        ValueError,
        match="not eligible for temporal comparison",
    ):
        compare_temporal_agent_observations(
            candidate,
            baseline,
        )


def test_temporal_comparison_rejects_different_observers():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000073"
        ),
        started_at_utc=datetime(
            2026,
            8,
            24,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        observer_id="observer-one",
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000074"
        ),
        started_at_utc=datetime(
            2026,
            8,
            25,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        observer_id="observer-two",
    )

    with pytest.raises(
        ValueError,
        match="same observer_id",
    ):
        compare_temporal_agent_observations(
            candidate,
            baseline,
        )


def test_temporal_comparison_rejects_different_regions():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000075"
        ),
        started_at_utc=datetime(
            2026,
            8,
            24,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        region_code="CL-Los-Lagos",
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000076"
        ),
        started_at_utc=datetime(
            2026,
            8,
            25,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        region_code="CL-Aysen",
    )

    with pytest.raises(
        ValueError,
        match="same region_code",
    ):
        compare_temporal_agent_observations(
            candidate,
            baseline,
        )


def test_temporal_comparison_requires_candidate_after_baseline():
    observed_at = datetime(
        2026,
        8,
        25,
        20,
        0,
        tzinfo=timezone.utc,
    )

    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000077"
        ),
        started_at_utc=observed_at,
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000078"
        ),
        started_at_utc=observed_at,
    )

    with pytest.raises(
        ValueError,
        match="occur after the baseline",
    ):
        compare_temporal_agent_observations(
            candidate,
            baseline,
        )
