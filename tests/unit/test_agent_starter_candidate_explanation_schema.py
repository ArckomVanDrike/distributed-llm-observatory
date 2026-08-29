import pytest
from pydantic import ValidationError

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
                reason=(
                    "Fixture evidence supports the candidate "
                    "assessment."
                ),
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


def test_candidate_explanation_accepts_recommended_why_projection():
    from schemas.agent_starter_report import (
        AgentStarterCandidateExplanation,
    )

    assessment = _assessment(
        architecture_id="local-agent",
        verdict=RecommendationVerdict.RECOMMENDED,
    )

    explanation = AgentStarterCandidateExplanation(
        assessment=assessment,
        concrete_stack=_stack("local-agent"),
        why=assessment.recommendation_reasons,
        why_not=[],
    )

    assert explanation.why == assessment.recommendation_reasons
    assert explanation.why_not == []
    assert explanation.assessment == assessment


def test_candidate_explanation_accepts_not_recommended_why_not_projection():
    from schemas.agent_starter_report import (
        AgentStarterCandidateExplanation,
    )

    assessment = _assessment(
        architecture_id="remote-agent",
        verdict=RecommendationVerdict.NOT_RECOMMENDED,
    )

    explanation = AgentStarterCandidateExplanation(
        assessment=assessment,
        concrete_stack=_stack("remote-agent"),
        why=[],
        why_not=assessment.recommendation_reasons,
    )

    assert explanation.why == []
    assert explanation.why_not == assessment.recommendation_reasons


def test_candidate_explanation_rejects_invented_reason():
    from schemas.agent_starter_report import (
        AgentStarterCandidateExplanation,
    )

    assessment = _assessment(
        architecture_id="local-agent",
        verdict=RecommendationVerdict.RECOMMENDED,
    )

    with pytest.raises(
        ValidationError,
        match="projection",
    ):
        AgentStarterCandidateExplanation(
            assessment=assessment,
            concrete_stack=_stack("local-agent"),
            why=[
                "A reason that was never produced by the decision engine.",
            ],
            why_not=[],
        )


def test_candidate_explanation_rejects_mismatched_stack():
    from schemas.agent_starter_report import (
        AgentStarterCandidateExplanation,
    )

    assessment = _assessment(
        architecture_id="local-agent",
        verdict=RecommendationVerdict.RECOMMENDED,
    )

    with pytest.raises(
        ValidationError,
        match="architecture",
    ):
        AgentStarterCandidateExplanation(
            assessment=assessment,
            concrete_stack=_stack("different-agent"),
            why=assessment.recommendation_reasons,
            why_not=[],
        )
