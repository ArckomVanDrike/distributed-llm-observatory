from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

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


def build_artifact() -> AgentLabRunArtifact:
    now = datetime(
        2026,
        8,
        24,
        20,
        0,
        tzinfo=timezone.utc,
    )

    session = AgentTestSession(
        target=TargetManifest(
            target_id="artifact-agent",
            display_name="Artifact Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        ),
        suite_id="agent-protocol-core",
        suite_version="0.1",
        status=AgentTestSessionStatus.COMPLETED,
        started_at_utc=now,
        completed_at_utc=now,
        selections=[],
        results=[],
    )

    report = AgentTechnicalReport(
        session_id=session.session_id,
        target_id=session.target.target_id,
        suite_id=session.suite_id,
        suite_version=session.suite_version,
        generated_at_utc=now,
        total_tasks=0,
        passed_tasks=0,
        failed_tasks=0,
        task_completion_rate=0.0,
        pass_rate=None,
        median_latency_ms=None,
        total_retries=0,
        total_human_interventions=0,
        findings=[
            "No benchmark task results are present in this session."
        ],
        recommendations=[
            "Run at least one compatible benchmark task before "
            "interpreting agent performance."
        ],
    )

    return AgentLabRunArtifact(
        session=session,
        technical_report=report,
    )


def test_agent_lab_run_artifact_round_trips_json():
    artifact = build_artifact()

    restored = AgentLabRunArtifact.model_validate_json(
        artifact.model_dump_json()
    )

    assert restored == artifact
    assert restored.schema_version == "0.1"
    assert (
        restored.technical_report.session_id
        == restored.session.session_id
    )


def test_agent_lab_run_artifact_rejects_mismatched_session_id():
    artifact = build_artifact()

    mismatched_report = artifact.technical_report.model_copy(
        update={
            "session_id": uuid4(),
        }
    )

    with pytest.raises(
        ValidationError,
        match="session_id",
    ):
        AgentLabRunArtifact(
            session=artifact.session,
            technical_report=mismatched_report,
        )


def test_agent_lab_run_artifact_rejects_mismatched_target_id():
    artifact = build_artifact()

    mismatched_report = artifact.technical_report.model_copy(
        update={
            "target_id": "different-agent",
        }
    )

    with pytest.raises(
        ValidationError,
        match="target_id",
    ):
        AgentLabRunArtifact(
            session=artifact.session,
            technical_report=mismatched_report,
        )


def test_agent_lab_run_artifact_rejects_mismatched_suite_id():
    artifact = build_artifact()

    mismatched_report = artifact.technical_report.model_copy(
        update={
            "suite_id": "different-suite",
        }
    )

    with pytest.raises(
        ValidationError,
        match="suite_id",
    ):
        AgentLabRunArtifact(
            session=artifact.session,
            technical_report=mismatched_report,
        )


def test_agent_lab_run_artifact_rejects_mismatched_suite_version():
    artifact = build_artifact()

    mismatched_report = artifact.technical_report.model_copy(
        update={
            "suite_version": "9.9",
        }
    )

    with pytest.raises(
        ValidationError,
        match="suite_version",
    ):
        AgentLabRunArtifact(
            session=artifact.session,
            technical_report=mismatched_report,
        )


def test_agent_lab_run_artifact_rejects_report_summary_mismatch():
    artifact = build_artifact()
    report = artifact.technical_report

    mismatched_report = AgentTechnicalReport(
        session_id=report.session_id,
        target_id=report.target_id,
        suite_id=report.suite_id,
        suite_version=report.suite_version,
        generated_at_utc=report.generated_at_utc,
        total_tasks=1,
        passed_tasks=1,
        failed_tasks=0,
        task_completion_rate=1.0,
        pass_rate=1.0,
        median_latency_ms=10.0,
        total_retries=0,
        total_human_interventions=0,
        findings=[],
        recommendations=[],
    )

    with pytest.raises(
        ValidationError,
        match="technical_report summary",
    ):
        AgentLabRunArtifact(
            session=artifact.session,
            technical_report=mismatched_report,
        )
