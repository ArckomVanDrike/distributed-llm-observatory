from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterConstraintConflict,
    AgentStarterGoal,
    AgentStarterPlan,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
    RecommendationVerdict,
)


def _shared_blocking_requirements(
    *,
    requirements: list[AgentStarterRequirement],
    candidate_assessments: list[
        CandidateArchitectureAssessment
    ],
) -> list[AgentStarterRequirement]:
    if not candidate_assessments:
        return []

    if any(
        candidate.recommendation
        is not RecommendationVerdict.NOT_RECOMMENDED
        for candidate in candidate_assessments
    ):
        return []

    return [
        requirement
        for requirement in requirements
        if all(
            requirement in candidate.blocking_requirements
            for candidate in candidate_assessments
        )
    ]


def build_agent_starter_plan(
    *,
    goal: AgentStarterGoal,
    requirements: list[AgentStarterRequirement],
    candidate_assessments: list[
        CandidateArchitectureAssessment
    ],
    constraint_conflict: AgentStarterConstraintConflict | None = None,
) -> AgentStarterPlan:
    resolved_conflict = constraint_conflict

    if resolved_conflict is None:
        shared_blockers = _shared_blocking_requirements(
            requirements=requirements,
            candidate_assessments=candidate_assessments,
        )

        if shared_blockers:
            resolved_conflict = AgentStarterConstraintConflict(
                conflicting_requirements=shared_blockers,
                summary=(
                    "All evaluated candidates are blocked by "
                    "the same hard requirement."
                ),
                resolution_options=[
                    "Change a conflicting hard requirement.",
                    (
                        "Evaluate another architecture that "
                        "satisfies the hard requirements."
                    ),
                ],
            )

    return AgentStarterPlan(
        goal=goal,
        requirements=requirements,
        candidate_assessments=candidate_assessments,
        constraint_conflict=resolved_conflict,
    )
