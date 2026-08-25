from datetime import datetime, timezone
from pathlib import Path

import pytest

from observer.core.agent_lab_artifact_io import (
    AgentLabArtifactIOError,
    load_agent_lab_run_artifact,
    write_agent_lab_run_artifact,
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


def build_artifact() -> AgentLabRunArtifact:
    now = datetime(
        2026,
        8,
        24,
        20,
        30,
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
    )

    return AgentLabRunArtifact(
        session=session,
        technical_report=report,
    )


def test_writer_persists_round_trippable_artifact(
    tmp_path: Path,
):
    artifact = build_artifact()
    output_path = tmp_path / "agent-run.json"

    write_agent_lab_run_artifact(
        artifact,
        output_path,
    )

    restored = AgentLabRunArtifact.model_validate_json(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert restored == artifact


def test_writer_replaces_existing_file(
    tmp_path: Path,
):
    artifact = build_artifact()
    output_path = tmp_path / "agent-run.json"

    output_path.write_text(
        "obsolete-content",
        encoding="utf-8",
    )

    write_agent_lab_run_artifact(
        artifact,
        output_path,
    )

    restored = AgentLabRunArtifact.model_validate_json(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert restored == artifact
    assert "obsolete-content" not in output_path.read_text(
        encoding="utf-8",
    )



def test_loader_restores_written_artifact(
    tmp_path: Path,
):
    artifact = build_artifact()
    output_path = tmp_path / "agent-run.json"

    write_agent_lab_run_artifact(
        artifact,
        output_path,
    )

    restored = load_agent_lab_run_artifact(
        output_path,
    )

    assert restored == artifact



def test_loader_rejects_missing_artifact(
    tmp_path: Path,
):
    path = tmp_path / "missing-agent-run.json"

    with pytest.raises(
        AgentLabArtifactIOError,
        match="Unable to read Agent Lab run artifact",
    ):
        load_agent_lab_run_artifact(path)


def test_loader_rejects_malformed_json(
    tmp_path: Path,
):
    path = tmp_path / "malformed-agent-run.json"
    path.write_text(
        "{not-json",
        encoding="utf-8",
    )

    with pytest.raises(
        AgentLabArtifactIOError,
        match="Invalid JSON in Agent Lab run artifact",
    ):
        load_agent_lab_run_artifact(path)


def test_loader_rejects_invalid_artifact_schema(
    tmp_path: Path,
):
    path = tmp_path / "invalid-agent-run.json"
    path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        AgentLabArtifactIOError,
        match="Invalid Agent Lab run artifact",
    ):
        load_agent_lab_run_artifact(path)
