from observer.core.agent_starter_decision_engine import (
    assess_coding_candidate,
    technical_feasibility_from_compatibility,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterRequirement,
    ConstraintStrength,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.compatibility import (
    AssessmentBasis,
    CompatibilityAssessment,
    CompatibilityVerdict,
)


def _assessment(
    verdict: CompatibilityVerdict,
) -> CompatibilityAssessment:
    return CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=verdict,
        summary="Compatibility result.",
    )


def _local_only_requirement() -> AgentStarterRequirement:
    evidence = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    return AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )


def test_compatible_maps_to_feasible():
    result = technical_feasibility_from_compatibility(
        _assessment(CompatibilityVerdict.COMPATIBLE)
    )

    assert result is TechnicalFeasibility.FEASIBLE


def test_constrained_maps_to_limited():
    result = technical_feasibility_from_compatibility(
        _assessment(CompatibilityVerdict.CONSTRAINED)
    )

    assert result is TechnicalFeasibility.LIMITED


def test_unknown_maps_to_unknown():
    result = technical_feasibility_from_compatibility(
        _assessment(CompatibilityVerdict.UNKNOWN)
    )

    assert result is TechnicalFeasibility.UNKNOWN


def test_hardware_not_recommended_does_not_become_agent_recommendation():
    result = technical_feasibility_from_compatibility(
        _assessment(
            CompatibilityVerdict.NOT_RECOMMENDED
        )
    )

    assert result is TechnicalFeasibility.LIMITED


def test_remote_coding_candidate_can_be_feasible_but_not_recommended():
    requirement = _local_only_requirement()

    remote_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The candidate architecture sends repository context "
            "to remote inference."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="cloud_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[remote_processing],
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.NOT_RECOMMENDED
    assert result.confidence is RecommendationConfidence.HIGH
    assert requirement.evidence[0] in result.supporting_evidence
    assert remote_processing in result.supporting_evidence


def test_local_coding_candidate_is_possible_not_automatically_recommended():
    requirement = _local_only_requirement()

    local_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "The candidate architecture keeps repository context "
            "inside the local execution boundary."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="local_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[local_processing],
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert result.recommendation is RecommendationVerdict.POSSIBLE
    assert result.confidence is RecommendationConfidence.MEDIUM
    assert requirement.evidence[0] in result.supporting_evidence
    assert local_processing in result.supporting_evidence


def test_limited_coding_candidate_is_possible_but_not_recommended():
    evidence = AgentStarterEvidence(
        key="local_execution_headroom",
        source=EvidenceSource.DERIVED,
        value="limited",
        reason=(
            "Compatibility evidence indicates limited "
            "execution headroom."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="local_coding",
        technical_feasibility=TechnicalFeasibility.LIMITED,
        requirements=[],
        candidate_evidence=[evidence],
    )

    assert result.technical_feasibility is TechnicalFeasibility.LIMITED
    assert (
        result.recommendation
        is RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.MEDIUM
    assert any(
        "limited" in reason.lower()
        for reason in result.technical_reasons
    )


def test_unknown_coding_feasibility_is_not_treated_as_feasible():
    evidence = AgentStarterEvidence(
        key="local_execution_headroom",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason=(
            "Available evidence is insufficient to establish "
            "local execution feasibility."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="local_coding",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        requirements=[],
        candidate_evidence=[evidence],
    )

    assert result.technical_feasibility is TechnicalFeasibility.UNKNOWN
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "unknown" in reason.lower()
        or "not established" in reason.lower()
        for reason in result.technical_reasons
    )


def test_not_feasible_coding_candidate_is_not_recommended():
    evidence = AgentStarterEvidence(
        key="local_execution_feasibility",
        source=EvidenceSource.DERIVED,
        value="not_feasible",
        reason=(
            "Observed constraints establish that the candidate "
            "cannot support the required local execution."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="local_coding",
        technical_feasibility=TechnicalFeasibility.NOT_FEASIBLE,
        requirements=[],
        candidate_evidence=[evidence],
    )

    assert (
        result.technical_feasibility
        is TechnicalFeasibility.NOT_FEASIBLE
    )
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.HIGH
    assert any(
        "not feasible" in reason.lower()
        for reason in result.technical_reasons
    )


def test_local_only_requirement_with_unknown_processing_is_not_recommended():
    requirement = _local_only_requirement()

    unknown_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason=(
            "It is not known whether the candidate sends "
            "repository context to remote inference."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="coding_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[unknown_processing],
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "cannot be verified" in reason.lower()
        or "insufficient" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_local_only_requirement_without_processing_evidence_is_not_recommended():
    requirement = _local_only_requirement()

    result = assess_coding_candidate(
        architecture_id="coding_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[],
    )

    assert result.technical_feasibility is TechnicalFeasibility.FEASIBLE
    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.confidence is RecommendationConfidence.LIMITED
    assert any(
        "cannot be verified" in reason.lower()
        or "insufficient" in reason.lower()
        for reason in result.recommendation_reasons
    )


def test_proven_local_only_violation_records_blocking_requirement():
    requirement = _local_only_requirement()

    remote_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The candidate architecture sends repository context "
            "to remote inference."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="cloud_coding",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[remote_processing],
    )

    assert result.blocking_requirements == [requirement]


def test_unknown_local_only_compliance_is_not_recorded_as_proven_blocker():
    requirement = _local_only_requirement()

    unknown_processing = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason=(
            "It is not known whether the candidate sends "
            "repository context to remote inference."
        ),
    )

    result = assess_coding_candidate(
        architecture_id="coding_candidate",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        requirements=[requirement],
        candidate_evidence=[unknown_processing],
    )

    assert (
        result.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )
    assert result.blocking_requirements == []
