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

    candidates = generate_agent_starter_candidates(prepared)

    if compatibility_by_architecture is not None:
        candidate_ids = {
            candidate.architecture_id
            for candidate in candidates
        }
        unknown_ids = (
            set(compatibility_by_architecture)
            - candidate_ids
        )

        if unknown_ids:
            raise ValueError(
                "Compatibility provided for unknown candidate "
                "architecture: "
                + ", ".join(sorted(unknown_ids))
            )

    for candidate in candidates:
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

        supporting_evidence = []

        for evidence in [
            *assessment.supporting_evidence,
            *feasibility.supporting_evidence,
        ]:
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
