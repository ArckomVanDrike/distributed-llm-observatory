from __future__ import annotations

from observer.core.agent_starter_candidate_generator import (
    generate_agent_starter_candidates,
)
from observer.core.agent_starter_decision_engine import (
    assess_agent_starter_candidate,
)
from observer.core.agent_starter_feasibility_evaluator import (
    evaluate_agent_starter_technical_feasibility,
)
from schemas.agent_starter import (
    AgentStarterPreparedInput,
    CandidateArchitectureAssessment,
)


def assess_agent_starter_candidates(
    *,
    prepared: AgentStarterPreparedInput,
) -> list[CandidateArchitectureAssessment]:
    assessments: list[CandidateArchitectureAssessment] = []

    for candidate in generate_agent_starter_candidates(prepared):
        feasibility = evaluate_agent_starter_technical_feasibility(
            prepared=prepared,
            candidate=candidate,
        )

        assessment = assess_agent_starter_candidate(
            goal=prepared.goal,
            architecture_id=candidate.architecture_id,
            technical_feasibility=(
                feasibility.technical_feasibility
            ),
            requirements=list(prepared.requirements),
            candidate_evidence=[
                *prepared.evidence,
                *candidate.evidence,
            ],
        )

        assessment = assessment.model_copy(
            update={
                "technical_reasons": list(feasibility.reasons),
            }
        )

        assessments.append(assessment)

    return assessments
