from datetime import datetime, timezone

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterPlan,
    CandidateArchitectureAssessment,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogArchitectureResult,
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
    AgentStarterCatalogQuery,
    AgentStarterCatalogQueryMatch,
)
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
)


def _assessment(
    architecture_id: str,
) -> CandidateArchitectureAssessment:
    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[
            "The architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The architecture is a possible option.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding architecture requires "
                    "a language model."
                ),
            ),
        ],
    )


def _entry(identifier: str) -> AgentStarterCatalogEntry:
    return AgentStarterCatalogEntry(
        identifier=identifier,
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="test-vendor",
        family="test-family",
        version="1.0",
        capabilities=[
            "coding",
        ],
        license="test-license",
        pricing_class="free",
        sources=[
            "https://example.com/catalog-entry",
        ],
        verified_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
    )


def _architecture_result(
    architecture_id: str,
    matched_entries: list[AgentStarterCatalogEntry],
) -> AgentStarterCatalogArchitectureResult:
    return AgentStarterCatalogArchitectureResult(
        architecture_id=architecture_id,
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        query_matches=[
            AgentStarterCatalogQueryMatch(
                architecture_id=architecture_id,
                catalog_snapshot_id=(
                    "agent-starter-catalog-v0-1"
                ),
                query=AgentStarterCatalogQuery(
                    component_type=(
                        AgentStarterCatalogComponentType.LLM
                    ),
                    required_capabilities=[
                        "coding",
                    ],
                ),
                matched_entries=matched_entries,
            ),
        ],
    )


def test_concrete_stack_orchestrator_preserves_all_architectures_in_order():
    from observer.core.agent_starter_concrete_stack_orchestrator import (
        build_agent_starter_concrete_stacks,
    )

    first_assessment = _assessment(
        "local-coding-agent",
    )
    second_assessment = _assessment(
        "cloud-coding-agent",
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=[
            first_assessment,
            second_assessment,
        ],
    )

    first_entry = _entry("coding-model-a")

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=plan,
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        architecture_results=[
            _architecture_result(
                "local-coding-agent",
                [
                    first_entry,
                ],
            ),
            _architecture_result(
                "cloud-coding-agent",
                [],
            ),
        ],
    )

    resolution = build_agent_starter_concrete_stacks(
        catalog_result,
    )

    assert resolution.catalog_result == catalog_result

    assert [
        stack.architecture_id
        for stack in resolution.stacks
    ] == [
        "local-coding-agent",
        "cloud-coding-agent",
    ]

    assert (
        resolution.stacks[0].components[0].selected_entry
        == first_entry
    )
    assert (
        resolution.stacks[1].components[0].selected_entry
        is None
    )

    assert all(
        stack.catalog_snapshot_id
        == "agent-starter-catalog-v0-1"
        for stack in resolution.stacks
    )


def test_concrete_stack_preserves_free_only_plan_requirement():
    from observer.core.agent_starter_concrete_stack_orchestrator import (
        build_agent_starter_concrete_stacks,
    )
    from schemas.agent_starter import (
        AgentStarterRequirement,
        ConstraintStrength,
    )

    assessment = _assessment(
        "local-coding-agent",
    )

    free_evidence = AgentStarterEvidence(
        key="free_components_only",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[
            AgentStarterRequirement(
                key="free_components_only",
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=[
                    free_evidence,
                ],
            ),
        ],
        candidate_assessments=[
            assessment,
        ],
    )

    free_entry = _entry(
        "free-coding-model",
    )

    architecture_result = AgentStarterCatalogArchitectureResult(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        query_matches=[
            AgentStarterCatalogQueryMatch(
                architecture_id="local-coding-agent",
                catalog_snapshot_id=(
                    "agent-starter-catalog-v0-1"
                ),
                query=AgentStarterCatalogQuery(
                    component_type=(
                        AgentStarterCatalogComponentType.LLM
                    ),
                    required_capabilities=[
                        "coding",
                    ],
                    required_pricing_class="free",
                ),
                matched_entries=[
                    free_entry,
                ],
            ),
        ],
    )

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=plan,
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        architecture_results=[
            architecture_result,
        ],
    )

    resolution = build_agent_starter_concrete_stacks(
        catalog_result
    )

    component = resolution.stacks[0].components[0]

    assert (
        component.requirement.required_pricing_class
        == "free"
    )
    assert component.selected_entry == free_entry
