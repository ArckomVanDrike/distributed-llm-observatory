from schemas.agent_starter import (
    AgentStarterEvidence,
    CandidateArchitectureAssessment,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
)


def _assessment(
    *,
    architecture_id: str,
    verdict: RecommendationVerdict,
) -> CandidateArchitectureAssessment:
    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=verdict,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The candidate is technically feasible.",
        ],
        recommendation_reasons=[
            "The recorded evidence supports this verdict.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="fixture_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Fixture evidence supports the assessment.",
            ),
        ],
    )


def _stack(
    architecture_id: str,
) -> AgentStarterConcreteStack:
    return AgentStarterConcreteStack(
        architecture_id=architecture_id,
        catalog_snapshot_id="catalog-v0-1",
    )


def test_builder_projects_recommended_reason_to_why():
    from observer.core.agent_starter_candidate_explanation_builder import (
        build_agent_starter_candidate_explanation,
    )

    assessment = _assessment(
        architecture_id="local-agent",
        verdict=RecommendationVerdict.RECOMMENDED,
    )

    result = build_agent_starter_candidate_explanation(
        assessment=assessment,
        concrete_stack=_stack("local-agent"),
    )

    assert result.assessment == assessment
    assert result.why == assessment.recommendation_reasons
    assert result.why_not == []


def test_builder_projects_possible_reason_to_why():
    from observer.core.agent_starter_candidate_explanation_builder import (
        build_agent_starter_candidate_explanation,
    )

    assessment = _assessment(
        architecture_id="possible-agent",
        verdict=RecommendationVerdict.POSSIBLE,
    )

    result = build_agent_starter_candidate_explanation(
        assessment=assessment,
        concrete_stack=_stack("possible-agent"),
    )

    assert result.why == assessment.recommendation_reasons
    assert result.why_not == []


def test_builder_projects_possible_but_not_recommended_to_why_not():
    from observer.core.agent_starter_candidate_explanation_builder import (
        build_agent_starter_candidate_explanation,
    )

    assessment = _assessment(
        architecture_id="limited-agent",
        verdict=(
            RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED
        ),
    )

    result = build_agent_starter_candidate_explanation(
        assessment=assessment,
        concrete_stack=_stack("limited-agent"),
    )

    assert result.why == []
    assert result.why_not == assessment.recommendation_reasons


def test_builder_projects_not_recommended_to_why_not():
    from observer.core.agent_starter_candidate_explanation_builder import (
        build_agent_starter_candidate_explanation,
    )

    assessment = _assessment(
        architecture_id="rejected-agent",
        verdict=RecommendationVerdict.NOT_RECOMMENDED,
    )

    result = build_agent_starter_candidate_explanation(
        assessment=assessment,
        concrete_stack=_stack("rejected-agent"),
    )

    assert result.why == []
    assert result.why_not == assessment.recommendation_reasons
