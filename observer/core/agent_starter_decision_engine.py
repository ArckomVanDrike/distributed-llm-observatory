from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
    ConstraintStrength,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.compatibility import (
    CompatibilityAssessment,
    CompatibilityVerdict,
)


def technical_feasibility_from_compatibility(
    assessment: CompatibilityAssessment,
) -> TechnicalFeasibility:
    if assessment.verdict is CompatibilityVerdict.COMPATIBLE:
        return TechnicalFeasibility.FEASIBLE

    if assessment.verdict is CompatibilityVerdict.CONSTRAINED:
        return TechnicalFeasibility.LIMITED

    if assessment.verdict is CompatibilityVerdict.NOT_RECOMMENDED:
        return TechnicalFeasibility.LIMITED

    return TechnicalFeasibility.UNKNOWN


def assess_coding_candidate(
    *,
    architecture_id: str,
    technical_feasibility: TechnicalFeasibility,
    requirements: list[AgentStarterRequirement],
    candidate_evidence: list[AgentStarterEvidence],
) -> CandidateArchitectureAssessment:
    supporting_evidence = [
        evidence
        for requirement in requirements
        for evidence in requirement.evidence
    ]
    supporting_evidence.extend(candidate_evidence)

    local_only_required = any(
        requirement.key == "source_code_must_stay_local"
        and requirement.value is True
        and requirement.strength is ConstraintStrength.HARD
        for requirement in requirements
    )

    processing_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key == "source_code_remote_processing"
    ]

    remote_processing = any(
        evidence.value is True
        for evidence in processing_evidence
    )

    processing_boundary_unknown = (
        not processing_evidence
        or any(
            evidence.source is EvidenceSource.UNKNOWN
            or evidence.value is None
            for evidence in processing_evidence
        )
    )

    if technical_feasibility is TechnicalFeasibility.FEASIBLE:
        technical_reason = (
            "The candidate is technically feasible."
        )
    elif technical_feasibility is TechnicalFeasibility.LIMITED:
        technical_reason = (
            "The candidate has limited technical feasibility."
        )
    elif technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        technical_reason = (
            "The candidate is not feasible under the evaluated "
            "technical constraints."
        )
    else:
        technical_reason = (
            "Technical feasibility is unknown and has not "
            "been established."
        )

    if local_only_required and remote_processing:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate violates the hard requirement "
                "that source code must stay local."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.NOT_FEASIBLE:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate is not technically feasible "
                "under the evaluated constraints."
            ],
            supporting_evidence=supporting_evidence,
        )

    if local_only_required and processing_boundary_unknown:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Compliance with the hard local-only source-code "
                "requirement cannot be verified from the available "
                "evidence."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.LIMITED:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.MEDIUM,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Limited technical feasibility makes this "
                "candidate a possible but currently "
                "not recommended choice."
            ],
            supporting_evidence=supporting_evidence,
        )

    if technical_feasibility is TechnicalFeasibility.UNKNOWN:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to "
                "recommend this candidate."
            ],
            supporting_evidence=supporting_evidence,
        )

    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=technical_feasibility,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[technical_reason],
        recommendation_reasons=[
            "No evaluated hard coding constraint excludes "
            "the candidate."
        ],
        supporting_evidence=supporting_evidence,
    )
