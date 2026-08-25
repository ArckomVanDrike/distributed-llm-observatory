from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from observer.core.agent_lab_observation_pairs import (
    discover_geographic_agent_observation_pairs,
    discover_temporal_agent_observation_pairs,
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

BASE_TIME = datetime(
    2026,
    8,
    25,
    12,
    0,
    tzinfo=timezone.utc,
)


def build_artifact(
    *,
    session_id: str,
    observed_at: datetime,
    observer_id: str = "observer-test",
    region_code: str = "CL-Los-Lagos",
) -> AgentLabRunArtifact:
    session = AgentTestSession(
        session_id=UUID(session_id),
        observer_id=observer_id,
        region_code=region_code,
        target=TargetManifest(
            target_id="pair-agent",
            display_name="Pair Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id="agent-protocol-core",
        suite_version="1.0",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=observed_at,
        completed_at_utc=observed_at,
    )

    return AgentLabRunArtifact(
        session=session,
        technical_report=build_agent_technical_report(
            session,
            generated_at_utc=observed_at,
        ),
    )


def test_temporal_pair_discovery_reports_comparable_and_rejected_pairs():
    first = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000101"
        ),
        observed_at=BASE_TIME,
    )
    second = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000102"
        ),
        observed_at=BASE_TIME + timedelta(hours=1),
    )
    third = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000103"
        ),
        observed_at=BASE_TIME + timedelta(hours=2),
        region_code="CL-Aysen",
    )

    pairs = discover_temporal_agent_observation_pairs(
        [
            third,
            first,
            second,
        ]
    )

    assert len(pairs) == 3

    assert pairs[0].baseline_session_id == first.session.session_id
    assert pairs[0].candidate_session_id == second.session.session_id
    assert pairs[0].comparable is True
    assert pairs[0].reasons == ()
    assert pairs[0].baseline_started_at_utc == BASE_TIME
    assert pairs[0].candidate_started_at_utc == (
        BASE_TIME + timedelta(hours=1)
    )
    assert pairs[0].baseline_observer_id == "observer-test"
    assert pairs[0].candidate_observer_id == "observer-test"
    assert pairs[0].baseline_region_code == "CL-Los-Lagos"
    assert pairs[0].candidate_region_code == "CL-Los-Lagos"

    assert pairs[1].baseline_session_id == first.session.session_id
    assert pairs[1].candidate_session_id == third.session.session_id
    assert pairs[1].comparable is False
    assert pairs[1].reasons == (
        "Temporal comparison requires the same region_code.",
    )

    assert pairs[2].baseline_session_id == second.session.session_id
    assert pairs[2].candidate_session_id == third.session.session_id
    assert pairs[2].comparable is False
    assert pairs[2].reasons == (
        "Temporal comparison requires the same region_code.",
    )


def test_geographic_pair_discovery_reports_comparable_and_rejected_pairs():
    first = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000111"
        ),
        observed_at=BASE_TIME,
        observer_id="observer-los-lagos",
        region_code="CL-Los-Lagos",
    )
    second = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000112"
        ),
        observed_at=BASE_TIME + timedelta(minutes=5),
        observer_id="observer-aysen-one",
        region_code="CL-Aysen",
    )
    third = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000113"
        ),
        observed_at=BASE_TIME + timedelta(minutes=30),
        observer_id="observer-aysen-two",
        region_code="CL-Aysen",
    )

    pairs = discover_geographic_agent_observation_pairs(
        [
            third,
            first,
            second,
        ],
        max_observation_skew=timedelta(
            minutes=10,
        ),
    )

    assert len(pairs) == 3

    assert pairs[0].baseline_session_id == first.session.session_id
    assert pairs[0].candidate_session_id == second.session.session_id
    assert pairs[0].comparable is True
    assert pairs[0].reasons == ()
    assert pairs[0].baseline_started_at_utc == BASE_TIME
    assert pairs[0].candidate_started_at_utc == (
        BASE_TIME + timedelta(minutes=5)
    )
    assert (
        pairs[0].baseline_observer_id
        == "observer-los-lagos"
    )
    assert (
        pairs[0].candidate_observer_id
        == "observer-aysen-one"
    )
    assert (
        pairs[0].baseline_region_code
        == "CL-Los-Lagos"
    )
    assert (
        pairs[0].candidate_region_code
        == "CL-Aysen"
    )

    assert pairs[1].baseline_session_id == first.session.session_id
    assert pairs[1].candidate_session_id == third.session.session_id
    assert pairs[1].comparable is False
    assert pairs[1].reasons == (
        "Geographic comparison observation skew "
        "exceeds max_observation_skew.",
    )

    assert pairs[2].baseline_session_id == second.session.session_id
    assert pairs[2].candidate_session_id == third.session.session_id
    assert pairs[2].comparable is False
    assert pairs[2].reasons == (
        "Geographic comparison requires different "
        "region_code values.",
    )


def test_temporal_pair_discovery_keeps_legacy_pair_with_reason():
    legacy = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000121"
        ),
        observed_at=BASE_TIME,
    )
    modern = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000122"
        ),
        observed_at=BASE_TIME + timedelta(hours=1),
    )

    legacy_payload = legacy.model_dump(
        mode="json",
    )
    legacy_payload["session"]["observer_id"] = None

    legacy = AgentLabRunArtifact.model_validate(
        legacy_payload
    )

    pairs = discover_temporal_agent_observation_pairs(
        [
            modern,
            legacy,
        ]
    )

    assert len(pairs) == 1
    assert pairs[0].baseline_session_id == legacy.session.session_id
    assert pairs[0].candidate_session_id == modern.session.session_id
    assert pairs[0].comparable is False
    assert pairs[0].reasons == (
        "Baseline observation is not eligible "
        "for temporal comparison.",
    )


def test_geographic_pair_discovery_keeps_legacy_pair_with_reason():
    legacy = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000131"
        ),
        observed_at=BASE_TIME,
        observer_id="observer-legacy",
        region_code="CL-Los-Lagos",
    )
    modern = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000132"
        ),
        observed_at=BASE_TIME + timedelta(minutes=5),
        observer_id="observer-modern",
        region_code="CL-Aysen",
    )

    legacy_payload = legacy.model_dump(
        mode="json",
    )
    legacy_payload["session"]["region_code"] = None

    legacy = AgentLabRunArtifact.model_validate(
        legacy_payload
    )

    pairs = discover_geographic_agent_observation_pairs(
        [
            modern,
            legacy,
        ],
        max_observation_skew=timedelta(
            minutes=10,
        ),
    )

    assert len(pairs) == 1
    assert pairs[0].baseline_session_id == legacy.session.session_id
    assert pairs[0].candidate_session_id == modern.session.session_id
    assert pairs[0].comparable is False
    assert pairs[0].reasons == (
        "Baseline observation is not eligible "
        "for geographic comparison.",
    )


def test_geographic_pair_discovery_rejects_negative_max_skew():
    first = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000141"
        ),
        observed_at=BASE_TIME,
        observer_id="observer-one",
        region_code="CL-Los-Lagos",
    )
    second = build_artifact(
        session_id=(
            "00000000-0000-0000-0000-000000000142"
        ),
        observed_at=BASE_TIME + timedelta(minutes=5),
        observer_id="observer-two",
        region_code="CL-Aysen",
    )

    with pytest.raises(
        ValueError,
        match="max_observation_skew cannot be negative",
    ):
        discover_geographic_agent_observation_pairs(
            [
                first,
                second,
            ],
            max_observation_skew=timedelta(
                seconds=-1,
            ),
        )
