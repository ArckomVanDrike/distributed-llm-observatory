from __future__ import annotations

from observer.core.agent_starter_assessment_orchestrator import (
    assess_agent_starter_candidates,
)
from observer.core.agent_starter_catalog_pipeline import (
    run_agent_starter_catalog_matching,
)
from observer.core.agent_starter_concrete_stack_pipeline import (
    run_agent_starter_concrete_stack_pipeline,
)
from observer.core.agent_starter_final_report_pipeline import (
    run_agent_starter_final_report_pipeline,
)
from observer.core.agent_starter_input_orchestrator import (
    prepare_agent_starter_input,
)
from observer.core.agent_starter_plan_builder import (
    build_agent_starter_plan,
)
from schemas.agent_starter import AgentStarterIntake
from schemas.agent_starter_catalog import (
    AgentStarterCatalogSnapshot,
)
from schemas.agent_starter_report import (
    AgentStarterFinalReport,
)
from schemas.compatibility import CompatibilityAssessment


def run_agent_starter_unified_pipeline(
    *,
    intake: AgentStarterIntake,
    catalog_snapshot: AgentStarterCatalogSnapshot,
    compatibility_by_architecture: (
        dict[str, CompatibilityAssessment] | None
    ) = None,
) -> AgentStarterFinalReport:
    prepared = prepare_agent_starter_input(intake)

    candidate_assessments = assess_agent_starter_candidates(
        prepared=prepared,
        compatibility_by_architecture=(
            compatibility_by_architecture
        ),
    )

    plan = build_agent_starter_plan(
        goal=prepared.goal,
        requirements=list(prepared.requirements),
        candidate_assessments=candidate_assessments,
    )

    catalog_result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=catalog_snapshot,
        hardware_profile=prepared.hardware_profile,
    )

    classification = (
        run_agent_starter_concrete_stack_pipeline(
            catalog_result
        )
    )

    return run_agent_starter_final_report_pipeline(
        prepared=prepared,
        classification=classification,
        catalog_snapshot=catalog_snapshot,
    )
