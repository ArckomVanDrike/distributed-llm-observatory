from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterPreparedInput,
    AgentStarterTechnicalFeasibilityAssessment,
    TechnicalFeasibility,
)


def evaluate_agent_starter_technical_feasibility(
    *,
    prepared: AgentStarterPreparedInput,
    candidate: AgentStarterCandidateArchitecture,
) -> AgentStarterTechnicalFeasibilityAssessment:
    if candidate.goal is not prepared.goal:
        raise ValueError(
            "Candidate goal must match prepared input goal."
        )

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
