from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from schemas.agent_lab import AgentTechnicalReport

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


def test_technical_report_records_traceable_metrics():
    session_id = uuid4()

    report = AgentTechnicalReport(
        session_id=session_id,
        target_id="example-agent",
        suite_id="agent-core",
        suite_version="0.1",
        generated_at_utc=NOW,
        total_tasks=4,
        passed_tasks=3,
        failed_tasks=1,
        task_completion_rate=1.0,
        pass_rate=0.75,
        median_latency_ms=1200,
        total_retries=1,
        total_human_interventions=0,
        findings=[
            "Three of four evaluated tasks passed.",
        ],
        recommendations=[
            "Inspect the failed task before changing configuration.",
        ],
    )

    assert report.schema_version == "0.1"
    assert report.session_id == session_id
    assert report.pass_rate == 0.75
    assert report.total_tasks == 4


def test_report_counts_must_match_total():
    with pytest.raises(
        ValidationError,
        match="passed_tasks plus failed_tasks",
    ):
        AgentTechnicalReport(
            session_id=uuid4(),
            target_id="example-agent",
            suite_id="agent-core",
            suite_version="0.1",
            generated_at_utc=NOW,
            total_tasks=4,
            passed_tasks=2,
            failed_tasks=1,
            task_completion_rate=1.0,
            pass_rate=0.5,
        )


def test_report_pass_rate_must_match_counts():
    with pytest.raises(
        ValidationError,
        match="pass_rate",
    ):
        AgentTechnicalReport(
            session_id=uuid4(),
            target_id="example-agent",
            suite_id="agent-core",
            suite_version="0.1",
            generated_at_utc=NOW,
            total_tasks=4,
            passed_tasks=3,
            failed_tasks=1,
            task_completion_rate=1.0,
            pass_rate=0.5,
        )


def test_report_allows_empty_session_summary():
    report = AgentTechnicalReport(
        session_id=uuid4(),
        target_id="example-agent",
        suite_id="agent-core",
        suite_version="0.1",
        generated_at_utc=NOW,
        total_tasks=0,
        passed_tasks=0,
        failed_tasks=0,
        task_completion_rate=0.0,
        pass_rate=None,
    )

    assert report.pass_rate is None


def test_report_rejects_naive_generation_time():
    with pytest.raises(
        ValidationError,
        match="timezone-aware",
    ):
        AgentTechnicalReport(
            session_id=uuid4(),
            target_id="example-agent",
            suite_id="agent-core",
            suite_version="0.1",
            generated_at_utc=NOW.replace(tzinfo=None),
            total_tasks=0,
            passed_tasks=0,
            failed_tasks=0,
            task_completion_rate=0.0,
            pass_rate=None,
        )
