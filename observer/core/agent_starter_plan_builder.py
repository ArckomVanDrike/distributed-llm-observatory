from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterGoal,
    AgentStarterPlan,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
)


def build_agent_starter_plan(
    *,
    goal: AgentStarterGoal,
    requirements: list[AgentStarterRequirement],
    candidate_assessments: list[
        CandidateArchitectureAssessment
    ],
) -> AgentStarterPlan:
    return AgentStarterPlan(
        goal=goal,
        requirements=requirements,
        candidate_assessments=candidate_assessments,
    )
