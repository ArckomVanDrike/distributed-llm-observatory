from __future__ import annotations

from observer.core.agent_starter_assessment_orchestrator import (
    assess_agent_starter_candidates,
)
from observer.core.agent_starter_input_orchestrator import (
    prepare_agent_starter_input,
)
from observer.core.agent_starter_plan_builder import (
    build_agent_starter_plan,
)
from schemas.agent_starter import (
    AgentStarterIntake,
    AgentStarterPlan,
)
from schemas.compatibility import CompatibilityAssessment


def run_agent_starter_pipeline(
    *,
    intake: AgentStarterIntake,
    compatibility_by_architecture: (
        dict[str, CompatibilityAssessment] | None
    ) = None,
) -> AgentStarterPlan:
    prepared = prepare_agent_starter_input(intake)

    candidate_assessments = assess_agent_starter_candidates(
        prepared=prepared,
        compatibility_by_architecture=(
            compatibility_by_architecture
        ),
    )

    return build_agent_starter_plan(
        goal=prepared.goal,
        requirements=list(prepared.requirements),
        candidate_assessments=candidate_assessments,
    )
