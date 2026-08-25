from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from observer.core.agent_lab_observation_qualification import (
    qualify_agent_observation,
)
from observer.core.agent_lab_run_comparison import (
    AgentLabRunComparison,
    compare_agent_lab_runs,
)
from schemas.agent_lab import AgentLabRunArtifact


@dataclass(frozen=True)
class AgentTemporalComparison:
    observer_id: str
    region_code: str
    baseline_started_at_utc: datetime
    candidate_started_at_utc: datetime
    run_comparison: AgentLabRunComparison


def compare_temporal_agent_observations(
    candidate: AgentLabRunArtifact,
    baseline: AgentLabRunArtifact,
) -> AgentTemporalComparison:
    candidate_qualification = qualify_agent_observation(
        candidate
    )
    baseline_qualification = qualify_agent_observation(
        baseline
    )

    if not candidate_qualification.temporal_eligible:
        raise ValueError(
            "Candidate observation is not eligible "
            "for temporal comparison."
        )

    if not baseline_qualification.temporal_eligible:
        raise ValueError(
            "Baseline observation is not eligible "
            "for temporal comparison."
        )

    candidate_session = candidate.session
    baseline_session = baseline.session

    if (
        candidate_session.observer_id
        != baseline_session.observer_id
    ):
        raise ValueError(
            "Temporal comparison requires the same "
            "observer_id."
        )

    if (
        candidate_session.region_code
        != baseline_session.region_code
    ):
        raise ValueError(
            "Temporal comparison requires the same "
            "region_code."
        )

    if (
        candidate_session.started_at_utc
        <= baseline_session.started_at_utc
    ):
        raise ValueError(
            "Temporal comparison requires the candidate "
            "observation to occur after the baseline."
        )

    run_comparison = compare_agent_lab_runs(
        candidate,
        baseline,
    )

    observer_id = candidate_session.observer_id
    region_code = candidate_session.region_code

    if observer_id is None or region_code is None:
        raise ValueError(
            "Temporal comparison requires complete "
            "observer provenance."
        )

    return AgentTemporalComparison(
        observer_id=observer_id,
        region_code=region_code,
        baseline_started_at_utc=(
            baseline_session.started_at_utc
        ),
        candidate_started_at_utc=(
            candidate_session.started_at_utc
        ),
        run_comparison=run_comparison,
    )
