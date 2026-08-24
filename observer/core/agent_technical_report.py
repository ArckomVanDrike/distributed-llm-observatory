from __future__ import annotations

from datetime import datetime
from statistics import median

from schemas.agent_lab import (
    AgentTechnicalReport,
    AgentTestSession,
)


def build_agent_technical_report(
    session: AgentTestSession,
    *,
    generated_at_utc: datetime,
) -> AgentTechnicalReport:
    results = session.results
    total_tasks = len(results)

    passed_tasks = sum(
        1
        for result in results
        if result.evaluation.passed
    )
    failed_tasks = total_tasks - passed_tasks

    completed_tasks = sum(
        1
        for result in results
        if result.task_completed
    )

    task_completion_rate = (
        completed_tasks / total_tasks
        if total_tasks
        else 0.0
    )

    pass_rate = (
        passed_tasks / total_tasks
        if total_tasks
        else None
    )

    median_latency_ms = (
        float(
            median(
                result.latency_ms
                for result in results
            )
        )
        if results
        else None
    )

    total_retries = sum(
        result.retry_count
        for result in results
    )
    total_human_interventions = sum(
        result.human_intervention_count
        for result in results
    )

    findings: list[str] = []
    recommendations: list[str] = []

    if total_tasks == 0:
        findings.append(
            "No benchmark task results are present in this session."
        )
        recommendations.append(
            "Run at least one compatible benchmark task before "
            "interpreting agent performance."
        )
    else:
        findings.append(
            f"{passed_tasks} of {total_tasks} evaluated tasks passed."
        )
        findings.append(
            f"{completed_tasks} of {total_tasks} tasks reported "
            "completion."
        )

        if failed_tasks:
            recommendations.append(
                "Inspect failed task evaluations and their criterion "
                "evidence before changing the agent configuration."
            )

        if total_retries:
            recommendations.append(
                "Review tasks that required retries for reliability "
                "or orchestration issues."
            )

        if total_human_interventions:
            recommendations.append(
                "Review tasks requiring human intervention to identify "
                "opportunities for greater autonomy."
            )

    return AgentTechnicalReport(
        session_id=session.session_id,
        target_id=session.target.target_id,
        suite_id=session.suite_id,
        suite_version=session.suite_version,
        generated_at_utc=generated_at_utc,
        total_tasks=total_tasks,
        passed_tasks=passed_tasks,
        failed_tasks=failed_tasks,
        task_completion_rate=task_completion_rate,
        pass_rate=pass_rate,
        median_latency_ms=median_latency_ms,
        total_retries=total_retries,
        total_human_interventions=total_human_interventions,
        findings=findings,
        recommendations=recommendations,
    )
