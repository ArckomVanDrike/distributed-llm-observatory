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

    local_only_requirements = [
        requirement
        for requirement in requirements
        if requirement.key == "source_code_must_stay_local"
        and requirement.value is True
        and requirement.strength is ConstraintStrength.HARD
    ]
    local_only_required = bool(local_only_requirements)

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
            blocking_requirements=local_only_requirements,
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


def assess_automation_candidate(
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

    workflow_deterministic = any(
        evidence.key == "workflow_deterministic"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    semantic_interpretation_not_required = any(
        evidence.key == "semantic_interpretation_required"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    candidate_uses_llm = any(
        evidence.key == "candidate_uses_llm"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_does_not_use_llm = any(
        evidence.key == "candidate_uses_llm"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    required_decision_keys = {
        "workflow_deterministic",
        "semantic_interpretation_required",
        "candidate_uses_llm",
    }
    decision_evidence = [
        evidence
        for evidence in candidate_evidence
        if evidence.key in required_decision_keys
    ]
    observed_decision_keys = {
        evidence.key
        for evidence in decision_evidence
    }

    decision_evidence_incomplete = (
        observed_decision_keys != required_decision_keys
        or any(
            evidence.source is EvidenceSource.UNKNOWN
            or evidence.value is None
            for evidence in decision_evidence
        )
    )

    availability_24_7_required = any(
        evidence.key == "availability_24_7_required"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    candidate_explicitly_not_always_available = any(
        evidence.key == "candidate_always_available"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    high_impact_actions = any(
        evidence.key == "destructive_or_high_impact_actions"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    autonomous_execution = any(
        evidence.key == "candidate_executes_autonomously"
        and evidence.value is True
        for evidence in candidate_evidence
    )

    approval_explicitly_not_required = any(
        evidence.key == "human_approval_required"
        and evidence.value is False
        for evidence in candidate_evidence
    )

    technical_reason = (
        "The candidate is technically feasible."
    )

    if (
        high_impact_actions
        and autonomous_execution
        and approval_explicitly_not_required
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.NOT_RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Autonomous destructive or high-impact actions "
                "without human approval are not recommended."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        availability_24_7_required
        and candidate_explicitly_not_always_available
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The candidate cannot satisfy the requested 24/7 "
                "availability because its deployment is not "
                "continuously available."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        workflow_deterministic
        and semantic_interpretation_not_required
        and candidate_explicitly_does_not_use_llm
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.RECOMMENDED,
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "The workflow is deterministic and does not "
                "require semantic interpretation, so traditional "
                "automation is the simpler recommended architecture."
            ],
            supporting_evidence=supporting_evidence,
        )

    if (
        workflow_deterministic
        and semantic_interpretation_not_required
        and candidate_uses_llm
    ):
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=(
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
            ),
            confidence=RecommendationConfidence.HIGH,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "LLM inference is not required for this deterministic "
                "workflow and would add unnecessary complexity."
            ],
            supporting_evidence=supporting_evidence,
        )

    if decision_evidence_incomplete:
        return CandidateArchitectureAssessment(
            architecture_id=architecture_id,
            technical_feasibility=technical_feasibility,
            recommendation=RecommendationVerdict.POSSIBLE,
            confidence=RecommendationConfidence.LIMITED,
            technical_reasons=[technical_reason],
            recommendation_reasons=[
                "Available evidence is insufficient to establish "
                "whether AI is necessary for this automation."
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
            "The available automation evidence does not yet justify "
            "a stronger architecture recommendation."
        ],
        supporting_evidence=supporting_evidence,
    )
