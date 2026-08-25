from datetime import datetime, timezone

from observer.core.agent_lab_observation_qualification import (
    qualify_agent_observation,
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

NOW = datetime(
    2026,
    8,
    25,
    20,
    0,
    tzinfo=timezone.utc,
)


def build_artifact(
    *,
    observer_id: str | None,
    region_code: str | None,
) -> AgentLabRunArtifact:
    session = AgentTestSession(
        observer_id=observer_id,
        region_code=region_code,
        target=TargetManifest(
            target_id="observatory-agent",
            display_name="Observatory Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id="agent-protocol-core",
        suite_version="1.0",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=NOW,
        completed_at_utc=NOW,
    )

    report = AgentTechnicalReport(
        session_id=session.session_id,
        target_id=session.target.target_id,
        suite_id=session.suite_id,
        suite_version=session.suite_version,
        generated_at_utc=NOW,
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


def test_complete_observer_provenance_qualifies_observation():
    artifact = build_artifact(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
    )

    qualification = qualify_agent_observation(
        artifact
    )

    assert qualification.provenance_complete is True
    assert qualification.temporal_eligible is True
    assert qualification.geographic_eligible is True
    assert qualification.reasons == ()


def test_missing_observer_id_limits_observatory_use():
    artifact = build_artifact(
        observer_id=None,
        region_code="CL-Los-Lagos",
    )

    qualification = qualify_agent_observation(
        artifact
    )

    assert qualification.provenance_complete is False
    assert qualification.temporal_eligible is False
    assert qualification.geographic_eligible is False
    assert qualification.reasons == (
        "missing observer_id",
    )


def test_missing_region_code_limits_observatory_use():
    artifact = build_artifact(
        observer_id="observer-test",
        region_code=None,
    )

    qualification = qualify_agent_observation(
        artifact
    )

    assert qualification.provenance_complete is False
    assert qualification.temporal_eligible is False
    assert qualification.geographic_eligible is False
    assert qualification.reasons == (
        "missing region_code",
    )


def test_missing_all_provenance_reports_all_reasons():
    artifact = build_artifact(
        observer_id=None,
        region_code=None,
    )

    qualification = qualify_agent_observation(
        artifact
    )

    assert qualification.provenance_complete is False
    assert qualification.temporal_eligible is False
    assert qualification.geographic_eligible is False
    assert qualification.reasons == (
        "missing observer_id",
        "missing region_code",
    )
