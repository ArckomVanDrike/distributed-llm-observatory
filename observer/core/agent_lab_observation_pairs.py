from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import combinations
from uuid import UUID

from observer.core.agent_lab_geographic_comparison import (
    compare_geographic_agent_observations,
)
from observer.core.agent_lab_temporal_comparison import (
    compare_temporal_agent_observations,
)
from schemas.agent_lab import AgentLabRunArtifact


@dataclass(frozen=True)
class TemporalAgentObservationPair:
    baseline_session_id: UUID
    candidate_session_id: UUID
    baseline_started_at_utc: datetime
    candidate_started_at_utc: datetime
    baseline_observer_id: str | None
    candidate_observer_id: str | None
    baseline_region_code: str | None
    candidate_region_code: str | None
    comparable: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GeographicAgentObservationPair:
    baseline_session_id: UUID
    candidate_session_id: UUID
    baseline_started_at_utc: datetime
    candidate_started_at_utc: datetime
    baseline_observer_id: str | None
    candidate_observer_id: str | None
    baseline_region_code: str | None
    candidate_region_code: str | None
    comparable: bool
    reasons: tuple[str, ...]


def _ordered_artifacts(
    artifacts: list[AgentLabRunArtifact],
) -> list[AgentLabRunArtifact]:
    return sorted(
        artifacts,
        key=lambda artifact: (
            artifact.session.started_at_utc,
            str(artifact.session.session_id),
        ),
    )


def discover_temporal_agent_observation_pairs(
    artifacts: list[AgentLabRunArtifact],
) -> list[TemporalAgentObservationPair]:
    ordered = _ordered_artifacts(artifacts)

    pairs: list[TemporalAgentObservationPair] = []

    for baseline, candidate in combinations(
        ordered,
        2,
    ):
        try:
            compare_temporal_agent_observations(
                candidate,
                baseline,
            )
        except ValueError as exc:
            comparable = False
            reasons = (str(exc),)
        else:
            comparable = True
            reasons = ()

        pairs.append(
            TemporalAgentObservationPair(
                baseline_session_id=(
                    baseline.session.session_id
                ),
                candidate_session_id=(
                    candidate.session.session_id
                ),
                baseline_started_at_utc=(
                    baseline.session.started_at_utc
                ),
                candidate_started_at_utc=(
                    candidate.session.started_at_utc
                ),
                baseline_observer_id=(
                    baseline.session.observer_id
                ),
                candidate_observer_id=(
                    candidate.session.observer_id
                ),
                baseline_region_code=(
                    baseline.session.region_code
                ),
                candidate_region_code=(
                    candidate.session.region_code
                ),
                comparable=comparable,
                reasons=reasons,
            )
        )

    return pairs


def discover_geographic_agent_observation_pairs(
    artifacts: list[AgentLabRunArtifact],
    *,
    max_observation_skew: timedelta,
) -> list[GeographicAgentObservationPair]:
    if max_observation_skew < timedelta(0):
        raise ValueError(
            "max_observation_skew cannot be negative."
        )

    ordered = _ordered_artifacts(artifacts)

    pairs: list[GeographicAgentObservationPair] = []

    for baseline, candidate in combinations(
        ordered,
        2,
    ):
        try:
            compare_geographic_agent_observations(
                candidate,
                baseline,
                max_observation_skew=max_observation_skew,
            )
        except ValueError as exc:
            comparable = False
            reasons = (str(exc),)
        else:
            comparable = True
            reasons = ()

        pairs.append(
            GeographicAgentObservationPair(
                baseline_session_id=(
                    baseline.session.session_id
                ),
                candidate_session_id=(
                    candidate.session.session_id
                ),
                baseline_started_at_utc=(
                    baseline.session.started_at_utc
                ),
                candidate_started_at_utc=(
                    candidate.session.started_at_utc
                ),
                baseline_observer_id=(
                    baseline.session.observer_id
                ),
                candidate_observer_id=(
                    candidate.session.observer_id
                ),
                baseline_region_code=(
                    baseline.session.region_code
                ),
                candidate_region_code=(
                    candidate.session.region_code
                ),
                comparable=comparable,
                reasons=reasons,
            )
        )

    return pairs
