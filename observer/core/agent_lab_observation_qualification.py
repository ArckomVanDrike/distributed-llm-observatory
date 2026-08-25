from __future__ import annotations

from dataclasses import dataclass

from schemas.agent_lab import AgentLabRunArtifact


@dataclass(frozen=True)
class AgentObservationQualification:
    provenance_complete: bool
    temporal_eligible: bool
    geographic_eligible: bool
    reasons: tuple[str, ...]


def qualify_agent_observation(
    artifact: AgentLabRunArtifact,
) -> AgentObservationQualification:
    reasons: list[str] = []

    if artifact.session.observer_id is None:
        reasons.append("missing observer_id")

    if artifact.session.region_code is None:
        reasons.append("missing region_code")

    provenance_complete = not reasons

    return AgentObservationQualification(
        provenance_complete=provenance_complete,
        temporal_eligible=provenance_complete,
        geographic_eligible=provenance_complete,
        reasons=tuple(reasons),
    )
