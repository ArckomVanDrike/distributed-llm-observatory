from datetime import datetime, timezone

from observer.core.agent_starter_catalog_pipeline import (
    run_agent_starter_catalog_matching,
)
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
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
    AgentStarterCatalogSnapshot,
)


def test_catalog_pipeline_matches_all_plan_candidates_without_filtering():
    deterministic = CandidateArchitectureAssessment(
        architecture_id="traditional-deterministic-automation",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The deterministic architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "Deterministic automation satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="The candidate does not use an LLM.",
            ),
        ],
    )

    llm_automation = CandidateArchitectureAssessment(
        architecture_id="supervised-automation-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The LLM architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The LLM architecture is a possible alternative.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate uses an LLM.",
            ),
        ],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.AUTOMATION,
        requirements=[],
        candidate_assessments=[
            deterministic,
            llm_automation,
        ],
    )

    catalog_entry = AgentStarterCatalogEntry(
        identifier="automation-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/automation-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[catalog_entry],
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    assert result.plan == plan
    assert result.catalog_snapshot_id == "catalog-2026-08-28"

    assert [
        architecture.architecture_id
        for architecture in result.architecture_results
    ] == [
        "traditional-deterministic-automation",
        "supervised-automation-agent",
    ]

    assert result.architecture_results[0].query_matches == []

    llm_matches = (
        result.architecture_results[1]
        .query_matches[0]
        .matched_entries
    )

    assert [
        entry.identifier
        for entry in llm_matches
    ] == [
        "automation-model",
    ]


def test_catalog_pipeline_preserves_coding_query_with_zero_matches():
    assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The coding architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The coding architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding-agent architecture uses an LLM "
                    "for coding assistance."
                ),
            ),
            AgentStarterEvidence(
                key="source_code_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Source code remains inside the "
                    "user-controlled environment."
                ),
            ),
        ],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=[assessment],
    )

    non_matching_entry = AgentStarterCatalogEntry(
        identifier="general-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=[
            "general_chat",
        ],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/general-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[
            non_matching_entry,
        ],
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    assert len(result.architecture_results) == 1

    architecture_result = result.architecture_results[0]

    assert architecture_result.architecture_id == "local-coding-agent"
    assert len(architecture_result.query_matches) == 1

    query_match = architecture_result.query_matches[0]

    assert query_match.query.required_capabilities == [
        "coding",
    ]
    assert query_match.matched_entries == []
