from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterConstraintConflict,
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
    constraint_conflict: AgentStarterConstraintConflict | None = None,
) -> AgentStarterPlan:
    return AgentStarterPlan(
        goal=goal,
        requirements=requirements,
        candidate_assessments=candidate_assessments,
        constraint_conflict=constraint_conflict,
    )
