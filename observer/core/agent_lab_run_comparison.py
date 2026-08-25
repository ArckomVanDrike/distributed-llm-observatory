from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import median
from uuid import UUID

from schemas.agent_lab import AgentLabRunArtifact


class AgentTaskOutcomeTransition(str, Enum):
    UNCHANGED_PASS = "unchanged-pass"
    PASS_TO_FAIL = "pass-to-fail"
    FAIL_TO_PASS = "fail-to-pass"
    UNCHANGED_FAIL = "unchanged-fail"


@dataclass(frozen=True)
class AgentTaskRunChange:
    task_id: str
    baseline_passed: bool
    candidate_passed: bool
    transition: AgentTaskOutcomeTransition


@dataclass(frozen=True)
class AgentLabRunComparison:
    baseline_session_id: UUID
    candidate_session_id: UUID
    task_changes: tuple[AgentTaskRunChange, ...]
    total_tasks: int
    regressions: int
    improvements: int
    unchanged: int
    pass_rate_delta: float | None
    median_latency_ms_delta: float | None
    retry_delta: int
    human_intervention_delta: int


def validate_comparable_agent_lab_runs(
    candidate: AgentLabRunArtifact,
    baseline: AgentLabRunArtifact,
) -> None:
    candidate_session = candidate.session
    baseline_session = baseline.session

    if (
        candidate_session.session_id
        == baseline_session.session_id
    ):
        raise ValueError(
            "Cannot compare the same session "
            "against itself."
        )

    if (
        candidate_session.target.target_id
        != baseline_session.target.target_id
    ):
        raise ValueError(
            "Cannot compare Agent Lab runs from "
            "different targets."
        )

    if (
        candidate_session.suite_id
        != baseline_session.suite_id
    ):
        raise ValueError(
            "Cannot compare Agent Lab runs from "
            "different suites."
        )

    if (
        candidate_session.suite_version
        != baseline_session.suite_version
    ):
        raise ValueError(
            "Cannot compare Agent Lab runs from "
            "different suite versions."
        )

    candidate_task_ids = {
        result.task_id
        for result in candidate_session.results
    }
    baseline_task_ids = {
        result.task_id
        for result in baseline_session.results
    }

    if candidate_task_ids != baseline_task_ids:
        raise ValueError(
            "Cannot compare Agent Lab runs with "
            "different task coverage."
        )


def classify_task_transition(
    *,
    baseline_passed: bool,
    candidate_passed: bool,
) -> AgentTaskOutcomeTransition:
    if baseline_passed and candidate_passed:
        return AgentTaskOutcomeTransition.UNCHANGED_PASS

    if baseline_passed and not candidate_passed:
        return AgentTaskOutcomeTransition.PASS_TO_FAIL

    if not baseline_passed and candidate_passed:
        return AgentTaskOutcomeTransition.FAIL_TO_PASS

    return AgentTaskOutcomeTransition.UNCHANGED_FAIL


def observed_pass_rate(
    artifact: AgentLabRunArtifact,
) -> float | None:
    results = artifact.session.results

    if not results:
        return None

    return (
        sum(
            result.evaluation.passed
            for result in results
        )
        / len(results)
    )


def observed_median_latency_ms(
    artifact: AgentLabRunArtifact,
) -> float | None:
    results = artifact.session.results

    if not results:
        return None

    return float(
        median(
            result.latency_ms
            for result in results
        )
    )


def compare_agent_lab_runs(
    candidate: AgentLabRunArtifact,
    baseline: AgentLabRunArtifact,
) -> AgentLabRunComparison:
    validate_comparable_agent_lab_runs(
        candidate,
        baseline,
    )

    candidate_results = {
        result.task_id: result
        for result in candidate.session.results
    }
    baseline_results = {
        result.task_id: result
        for result in baseline.session.results
    }

    task_changes = []

    for task_id in sorted(baseline_results):
        baseline_passed = (
            baseline_results[
                task_id
            ].evaluation.passed
        )
        candidate_passed = (
            candidate_results[
                task_id
            ].evaluation.passed
        )

        task_changes.append(
            AgentTaskRunChange(
                task_id=task_id,
                baseline_passed=baseline_passed,
                candidate_passed=candidate_passed,
                transition=classify_task_transition(
                    baseline_passed=baseline_passed,
                    candidate_passed=candidate_passed,
                ),
            )
        )

    regressions = sum(
        change.transition
        is AgentTaskOutcomeTransition.PASS_TO_FAIL
        for change in task_changes
    )
    improvements = sum(
        change.transition
        is AgentTaskOutcomeTransition.FAIL_TO_PASS
        for change in task_changes
    )
    unchanged = (
        len(task_changes)
        - regressions
        - improvements
    )

    candidate_pass_rate = observed_pass_rate(
        candidate
    )
    baseline_pass_rate = observed_pass_rate(
        baseline
    )

    pass_rate_delta = (
        candidate_pass_rate - baseline_pass_rate
        if (
            candidate_pass_rate is not None
            and baseline_pass_rate is not None
        )
        else None
    )

    candidate_latency = observed_median_latency_ms(
        candidate
    )
    baseline_latency = observed_median_latency_ms(
        baseline
    )

    median_latency_ms_delta = (
        candidate_latency - baseline_latency
        if (
            candidate_latency is not None
            and baseline_latency is not None
        )
        else None
    )

    retry_delta = (
        sum(
            result.retry_count
            for result in candidate.session.results
        )
        - sum(
            result.retry_count
            for result in baseline.session.results
        )
    )

    human_intervention_delta = (
        sum(
            result.human_intervention_count
            for result in candidate.session.results
        )
        - sum(
            result.human_intervention_count
            for result in baseline.session.results
        )
    )

    return AgentLabRunComparison(
        baseline_session_id=(
            baseline.session.session_id
        ),
        candidate_session_id=(
            candidate.session.session_id
        ),
        task_changes=tuple(task_changes),
        total_tasks=len(task_changes),
        regressions=regressions,
        improvements=improvements,
        unchanged=unchanged,
        pass_rate_delta=pass_rate_delta,
        median_latency_ms_delta=(
            median_latency_ms_delta
        ),
        retry_delta=retry_delta,
        human_intervention_delta=(
            human_intervention_delta
        ),
    )
