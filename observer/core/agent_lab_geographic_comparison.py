from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from observer.core.agent_lab_observation_qualification import (
    qualify_agent_observation,
)
from observer.core.agent_lab_run_comparison import (
    AgentLabRunComparison,
    compare_agent_lab_runs,
)
from schemas.agent_lab import AgentLabRunArtifact


@dataclass(frozen=True)
class AgentGeographicComparison:
    baseline_observer_id: str
    candidate_observer_id: str

    baseline_region_code: str
    candidate_region_code: str

    baseline_started_at_utc: datetime
    candidate_started_at_utc: datetime

    observation_skew: timedelta
    max_observation_skew: timedelta

    run_comparison: AgentLabRunComparison


def compare_geographic_agent_observations(
    candidate: AgentLabRunArtifact,
    baseline: AgentLabRunArtifact,
    *,
    max_observation_skew: timedelta,
) -> AgentGeographicComparison:
    if max_observation_skew < timedelta(0):
        raise ValueError(
            "max_observation_skew cannot be negative."
        )

    candidate_qualification = qualify_agent_observation(
        candidate
    )
    baseline_qualification = qualify_agent_observation(
        baseline
    )

    if not candidate_qualification.geographic_eligible:
        raise ValueError(
            "Candidate observation is not eligible "
            "for geographic comparison."
        )

    if not baseline_qualification.geographic_eligible:
        raise ValueError(
            "Baseline observation is not eligible "
            "for geographic comparison."
        )

    candidate_session = candidate.session
    baseline_session = baseline.session

    if (
        candidate_session.region_code
        == baseline_session.region_code
    ):
        raise ValueError(
            "Geographic comparison requires different "
            "region_code values."
        )

    observation_skew = abs(
        candidate_session.started_at_utc
        - baseline_session.started_at_utc
    )

    if observation_skew > max_observation_skew:
        raise ValueError(
            "Geographic comparison observation skew "
            "exceeds max_observation_skew."
        )

    run_comparison = compare_agent_lab_runs(
        candidate,
        baseline,
    )

    candidate_observer_id = (
        candidate_session.observer_id
    )
    baseline_observer_id = (
        baseline_session.observer_id
    )
    candidate_region_code = (
        candidate_session.region_code
    )
    baseline_region_code = (
        baseline_session.region_code
    )

    if (
        candidate_observer_id is None
        or baseline_observer_id is None
        or candidate_region_code is None
        or baseline_region_code is None
    ):
        raise ValueError(
            "Geographic comparison requires complete "
            "observer provenance."
        )

    return AgentGeographicComparison(
        baseline_observer_id=baseline_observer_id,
        candidate_observer_id=candidate_observer_id,
        baseline_region_code=baseline_region_code,
        candidate_region_code=candidate_region_code,
        baseline_started_at_utc=(
            baseline_session.started_at_utc
        ),
        candidate_started_at_utc=(
            candidate_session.started_at_utc
        ),
        observation_skew=observation_skew,
        max_observation_skew=max_observation_skew,
        run_comparison=run_comparison,
    )
