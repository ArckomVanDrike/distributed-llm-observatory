from __future__ import annotations

from observer.core.agent_starter_candidate_explanation_builder import (
    build_agent_starter_candidate_explanation,
)
from schemas.agent_starter_report import (
    AgentStarterCandidateExplanation,
)
from schemas.agent_starter_result import (
    AgentStarterConcreteStackClassification,
)


def build_agent_starter_candidate_explanations(
    classification: AgentStarterConcreteStackClassification,
) -> list[AgentStarterCandidateExplanation]:
    assessments = list(
        classification.resolution.catalog_result.plan.candidate_assessments
    )
    stacks = list(
        classification.resolution.stacks
    )

    if len(assessments) != len(stacks):
        raise ValueError(
            "Candidate assessment count does not match "
            "concrete stack count."
        )

    explanations: list[AgentStarterCandidateExplanation] = []

    for assessment, concrete_stack in zip(
        assessments,
        stacks,
        strict=True,
    ):
        if assessment.architecture_id != concrete_stack.architecture_id:
            raise ValueError(
                "Candidate assessment must correspond to "
                "the concrete stack in the same position."
            )

        explanations.append(
            build_agent_starter_candidate_explanation(
                assessment=assessment,
                concrete_stack=concrete_stack,
            )
        )

    return explanations
