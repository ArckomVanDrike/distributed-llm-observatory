from __future__ import annotations

from observer.core.agent_starter_feasibility import (
    technical_feasibility_from_compatibility,
)
from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterEvidence,
    AgentStarterPreparedInput,
    AgentStarterTechnicalFeasibilityAssessment,
    EvidenceSource,
    TechnicalFeasibility,
)
from schemas.compatibility import CompatibilityAssessment


def evaluate_agent_starter_technical_feasibility(
    *,
    prepared: AgentStarterPreparedInput,
    candidate: AgentStarterCandidateArchitecture,
    compatibility_assessment: CompatibilityAssessment | None = None,
) -> AgentStarterTechnicalFeasibilityAssessment:
    if candidate.goal is not prepared.goal:
        raise ValueError(
            "Candidate goal must match prepared input goal."
        )

    if compatibility_assessment is None:
        return AgentStarterTechnicalFeasibilityAssessment(
            architecture_id=candidate.architecture_id,
            goal=candidate.goal,
            technical_feasibility=TechnicalFeasibility.UNKNOWN,
            reasons=[
                (
                    "Technical feasibility cannot be established "
                    "without candidate-specific technical requirements "
                    "or compatibility evidence."
                ),
            ],
        )

    technical_feasibility = (
        technical_feasibility_from_compatibility(
            compatibility_assessment
        )
    )

    compatibility_evidence = AgentStarterEvidence(
        key="candidate_compatibility_verdict",
        source=EvidenceSource.DERIVED,
        value=compatibility_assessment.verdict.value,
        reason=compatibility_assessment.summary,
    )

    return AgentStarterTechnicalFeasibilityAssessment(
        architecture_id=candidate.architecture_id,
        goal=candidate.goal,
        technical_feasibility=technical_feasibility,
        reasons=[
            compatibility_assessment.summary,
            *compatibility_assessment.reasons,
        ],
        supporting_evidence=[
            compatibility_evidence,
        ],
    )
