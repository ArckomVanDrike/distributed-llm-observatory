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
    verdict: RecommendationVerdict,
) -> CandidateArchitectureAssessment:
    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=verdict,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[
            "The architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The architecture has already been assessed.",
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


def _entry() -> AgentStarterCatalogEntry:
    return AgentStarterCatalogEntry(
        identifier="coding-model-a",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="test-vendor",
        family="test-family",
        version="1.0",
        capabilities=["coding"],
        license="test-license",
        pricing_class="free",
        sources=["https://example.com/model"],
        verified_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
    )


def _architecture_result(
    *,
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
                    required_capabilities=["coding"],
                ),
                matched_entries=matched_entries,
            ),
        ],
    )


def test_concrete_stack_pipeline_resolves_and_classifies_candidates():
    from observer.core.agent_starter_concrete_stack_pipeline import (
        run_agent_starter_concrete_stack_pipeline,
    )

    recommended = _assessment(
        "local-coding-agent",
        RecommendationVerdict.RECOMMENDED,
    )
    alternative = _assessment(
        "cloud-coding-agent",
        RecommendationVerdict.POSSIBLE,
    )

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=AgentStarterPlan(
            goal=AgentStarterGoal.CODING,
            candidate_assessments=[
                recommended,
                alternative,
            ],
        ),
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        architecture_results=[
            _architecture_result(
                architecture_id="local-coding-agent",
                matched_entries=[_entry()],
            ),
            _architecture_result(
                architecture_id="cloud-coding-agent",
                matched_entries=[],
            ),
        ],
    )

    result = run_agent_starter_concrete_stack_pipeline(
        catalog_result
    )

    assert result.resolution.catalog_result == catalog_result

    assert [
        stack.architecture_id
        for stack in result.resolution.stacks
    ] == [
        "local-coding-agent",
        "cloud-coding-agent",
    ]

    assert result.recommended_architecture_ids == [
        "local-coding-agent",
    ]
    assert result.possible_architecture_ids == [
        "cloud-coding-agent",
    ]

    assert (
        result.resolution.stacks[0]
        .components[0]
        .selected_entry
        .identifier
        == "coding-model-a"
    )

    assert (
        result.resolution.stacks[1]
        .components[0]
        .selected_entry
        is None
    )


def test_concrete_stack_pipeline_preserves_paid_external_service_classification():
    from observer.core.agent_starter_catalog_pipeline import (
        run_agent_starter_catalog_matching,
    )
    from observer.core.agent_starter_concrete_stack_pipeline import (
        run_agent_starter_concrete_stack_pipeline,
    )
    from schemas.agent_starter import (
        AgentStarterRequirement,
        ConstraintStrength,
    )
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogSnapshot,
    )

    assessment = _assessment(
        "local-coding-agent",
        RecommendationVerdict.RECOMMENDED,
    )

    constraint_evidence = AgentStarterEvidence(
        key="paid_external_services_allowed",
        source=EvidenceSource.DECLARED,
        value=False,
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[
            AgentStarterRequirement(
                key="paid_external_services_allowed",
                value=False,
                strength=ConstraintStrength.HARD,
                evidence=[
                    constraint_evidence,
                ],
            ),
        ],
        candidate_assessments=[
            assessment,
        ],
    )

    def catalog_entry(
        identifier: str,
        *,
        pricing: str,
    ) -> AgentStarterCatalogEntry:
        return AgentStarterCatalogEntry.model_validate(
            {
                "schema_version": "0.2",
                "identifier": identifier,
                "component_type": "llm",
                "vendor": "Example Vendor",
                "family": "Example",
                "version": "1.0",
                "capabilities": [
                    "coding",
                ],
                "deployment_modes": [
                    "remote",
                ],
                "license": "example-license",
                "pricing_class": "free",
                "access_options": [
                    {
                        "deployment_mode": "remote",
                        "access_kind": "external_service",
                        "pricing": pricing,
                    },
                ],
                "sources": [
                    f"https://example.invalid/{identifier}",
                ],
                "verified_at": datetime(
                    2026,
                    8,
                    29,
                    tzinfo=timezone.utc,
                ),
            }
        )

    free_service = catalog_entry(
        "free-service",
        pricing="free",
    )
    unknown_service = catalog_entry(
        "unknown-service",
        pricing="provider_dependent",
    )
    paid_service = catalog_entry(
        "paid-service",
        pricing="usage_based",
    )

    snapshot = AgentStarterCatalogSnapshot(
        schema_version="0.2",
        snapshot_id="catalog-v0-2-cost-test",
        generated_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
        entries=[
            free_service,
            unknown_service,
            paid_service,
        ],
    )

    catalog_result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    classification = (
        run_agent_starter_concrete_stack_pipeline(
            catalog_result
        )
    )

    component = (
        classification
        .resolution
        .stacks[0]
        .components[0]
    )

    assert [
        entry.identifier
        for entry in component.matched_entries
    ] == [
        "free-service",
    ]

    assert [
        entry.identifier
        for entry in component.indeterminate_entries
    ] == [
        "unknown-service",
    ]

    assert [
        entry.identifier
        for entry in component.constraint_excluded_entries
    ] == [
        "paid-service",
    ]

    assert component.selected_entry == free_service
