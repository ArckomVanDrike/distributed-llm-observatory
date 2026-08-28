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
from schemas.compatibility import CompatibilityAssessment


def assess_agent_starter_candidates(
    *,
    prepared: AgentStarterPreparedInput,
    compatibility_by_architecture: (
        dict[str, CompatibilityAssessment] | None
    ) = None,
) -> list[CandidateArchitectureAssessment]:
    assessments: list[CandidateArchitectureAssessment] = []

    for candidate in generate_agent_starter_candidates(prepared):
        compatibility_assessment = None
        if compatibility_by_architecture is not None:
            compatibility_assessment = (
                compatibility_by_architecture.get(
                    candidate.architecture_id
                )
            )

        feasibility = evaluate_agent_starter_technical_feasibility(
            prepared=prepared,
            candidate=candidate,
            compatibility_assessment=compatibility_assessment,
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

        supporting_evidence = list(
            assessment.supporting_evidence
        )

        for evidence in feasibility.supporting_evidence:
            if evidence not in supporting_evidence:
                supporting_evidence.append(evidence)

        assessment = assessment.model_copy(
            update={
                "technical_reasons": list(feasibility.reasons),
                "supporting_evidence": supporting_evidence,
            }
        )

        assessments.append(assessment)

    return assessments
