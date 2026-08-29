from __future__ import annotations

from schemas.agent_starter import (
    CandidateArchitectureAssessment,
    RecommendationVerdict,
)
from schemas.agent_starter_report import (
    AgentStarterCandidateExplanation,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
)


def build_agent_starter_candidate_explanation(
    *,
    assessment: CandidateArchitectureAssessment,
    concrete_stack: AgentStarterConcreteStack,
) -> AgentStarterCandidateExplanation:
    recommendation_reasons = list(
        assessment.recommendation_reasons
    )

    if assessment.recommendation in {
        RecommendationVerdict.RECOMMENDED,
        RecommendationVerdict.POSSIBLE,
    }:
        why = recommendation_reasons
        why_not: list[str] = []
    else:
        why = []
        why_not = recommendation_reasons

    return AgentStarterCandidateExplanation(
        assessment=assessment,
        concrete_stack=concrete_stack,
        why=why,
        why_not=why_not,
    )
