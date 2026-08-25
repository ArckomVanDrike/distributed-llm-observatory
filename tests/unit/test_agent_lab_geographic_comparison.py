from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from observer.core.agent_lab_geographic_comparison import (
    compare_geographic_agent_observations,
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
    observer_id: str,
    region_code: str,
) -> AgentLabRunArtifact:
    session = AgentTestSession(
        session_id=UUID(session_id),
        observer_id=observer_id,
        region_code=region_code,
        target=TargetManifest(
            target_id="geographic-agent",
            display_name="Geographic Agent",
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


def test_geographic_comparison_preserves_observation_context():
    baseline_time = datetime(
        2026,
        8,
        25,
        20,
        0,
        tzinfo=timezone.utc,
    )
    candidate_time = baseline_time + timedelta(
        minutes=5,
    )

    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000081"
        ),
        started_at_utc=baseline_time,
        observer_id="observer-los-lagos",
        region_code="CL-Los-Lagos",
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000082"
        ),
        started_at_utc=candidate_time,
        observer_id="observer-aysen",
        region_code="CL-Aysen",
    )

    result = compare_geographic_agent_observations(
        candidate,
        baseline,
        max_observation_skew=timedelta(
            minutes=10,
        ),
    )

    assert result.baseline_observer_id == (
        "observer-los-lagos"
    )
    assert result.candidate_observer_id == (
        "observer-aysen"
    )

    assert result.baseline_region_code == (
        "CL-Los-Lagos"
    )
    assert result.candidate_region_code == (
        "CL-Aysen"
    )

    assert result.baseline_started_at_utc == baseline_time
    assert result.candidate_started_at_utc == candidate_time
    assert result.observation_skew == timedelta(
        minutes=5,
    )
    assert result.max_observation_skew == timedelta(
        minutes=10,
    )

    assert result.run_comparison.total_tasks == 0


def test_geographic_comparison_rejects_incomplete_provenance():
    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000091"
        ),
        started_at_utc=datetime(
            2026,
            8,
            25,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        observer_id="observer-one",
        region_code="CL-Los-Lagos",
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000092"
        ),
        started_at_utc=datetime(
            2026,
            8,
            25,
            20,
            5,
            tzinfo=timezone.utc,
        ),
        observer_id=None,
        region_code="CL-Aysen",
    )

    with pytest.raises(
        ValueError,
        match="not eligible for geographic comparison",
    ):
        compare_geographic_agent_observations(
            candidate,
            baseline,
            max_observation_skew=timedelta(
                minutes=10,
            ),
        )


def test_geographic_comparison_requires_different_regions():
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
            "00000000-0000-0000-0000-000000000093"
        ),
        started_at_utc=observed_at,
        observer_id="observer-one",
        region_code="CL-Los-Lagos",
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000094"
        ),
        started_at_utc=observed_at,
        observer_id="observer-two",
        region_code="CL-Los-Lagos",
    )

    with pytest.raises(
        ValueError,
        match="different region_code",
    ):
        compare_geographic_agent_observations(
            candidate,
            baseline,
            max_observation_skew=timedelta(
                minutes=10,
            ),
        )


def test_geographic_comparison_rejects_excessive_observation_skew():
    baseline_time = datetime(
        2026,
        8,
        25,
        20,
        0,
        tzinfo=timezone.utc,
    )
    candidate_time = baseline_time + timedelta(
        minutes=30,
    )

    baseline = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000095"
        ),
        started_at_utc=baseline_time,
        observer_id="observer-one",
        region_code="CL-Los-Lagos",
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000096"
        ),
        started_at_utc=candidate_time,
        observer_id="observer-two",
        region_code="CL-Aysen",
    )

    with pytest.raises(
        ValueError,
        match="exceeds max_observation_skew",
    ):
        compare_geographic_agent_observations(
            candidate,
            baseline,
            max_observation_skew=timedelta(
                minutes=10,
            ),
        )


def test_geographic_comparison_rejects_negative_max_skew():
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
            "00000000-0000-0000-0000-000000000097"
        ),
        started_at_utc=observed_at,
        observer_id="observer-one",
        region_code="CL-Los-Lagos",
    )
    candidate = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000098"
        ),
        started_at_utc=observed_at,
        observer_id="observer-two",
        region_code="CL-Aysen",
    )

    with pytest.raises(
        ValueError,
        match="max_observation_skew cannot be negative",
    ):
        compare_geographic_agent_observations(
            candidate,
            baseline,
            max_observation_skew=timedelta(
                seconds=-1,
            ),
        )
