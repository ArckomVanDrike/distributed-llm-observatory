from datetime import datetime, timezone

from observer.core.agent_starter_catalog_orchestrator import (
    match_agent_starter_architecture_to_catalog,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
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


def _entry(
    *,
    identifier: str,
    capabilities: list[str],
) -> AgentStarterCatalogEntry:
    return AgentStarterCatalogEntry(
        identifier=identifier,
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=capabilities,
        license="example-license",
        pricing_class="free",
        sources=[
            f"https://example.invalid/{identifier}",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )


def test_catalog_orchestrator_matches_coding_architecture():
    first_match = _entry(
        identifier="coding-model-a",
        capabilities=["coding", "tool_use"],
    )
    non_match = _entry(
        identifier="general-model",
        capabilities=["general_chat"],
    )
    second_match = _entry(
        identifier="coding-model-b",
        capabilities=["coding"],
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
            first_match,
            non_match,
            second_match,
        ],
    )

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
                key="source_code_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Source code remains inside the "
                    "user-controlled environment."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding-agent architecture requires "
                    "a language model."
                ),
            ),
        ],
    )

    result = match_agent_starter_architecture_to_catalog(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
        snapshot=snapshot,
    )

    assert result.architecture_id == "local-coding-agent"
    assert result.catalog_snapshot_id == "catalog-2026-08-28"
    assert len(result.query_matches) == 1

    query_match = result.query_matches[0]

    assert query_match.architecture_id == "local-coding-agent"
    assert (
        query_match.catalog_snapshot_id
        == "catalog-2026-08-28"
    )
    assert query_match.query.required_capabilities == ["coding"]
    assert [
        entry.identifier
        for entry in query_match.matched_entries
    ] == [
        "coding-model-a",
        "coding-model-b",
    ]


def test_catalog_orchestrator_preserves_deterministic_automation_without_queries():
    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[],
    )

    assessment = CandidateArchitectureAssessment(
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
                reason=(
                    "The deterministic automation architecture "
                    "does not use an LLM."
                ),
            ),
        ],
    )

    result = match_agent_starter_architecture_to_catalog(
        goal=AgentStarterGoal.AUTOMATION,
        assessment=assessment,
        snapshot=snapshot,
    )

    assert (
        result.architecture_id
        == "traditional-deterministic-automation"
    )
    assert result.catalog_snapshot_id == "catalog-2026-08-28"
    assert result.query_matches == []


def test_catalog_orchestrator_preserves_query_with_zero_matches():
    non_matching = _entry(
        identifier="general-model",
        capabilities=[
            "general_chat",
        ],
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
            non_matching,
        ],
    )

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
                key="source_code_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Source code remains inside the "
                    "user-controlled environment."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding-agent architecture requires "
                    "a language model."
                ),
            ),
        ],
    )

    result = match_agent_starter_architecture_to_catalog(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
        snapshot=snapshot,
    )

    assert len(result.query_matches) == 1

    query_match = result.query_matches[0]

    assert query_match.query.required_capabilities == [
        "coding",
    ]
    assert query_match.matched_entries == []


def test_catalog_orchestrator_preserves_all_candidate_assessments_in_order():
    llm = _entry(
        identifier="automation-model",
        capabilities=[],
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[llm],
    )

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

    from observer.core.agent_starter_catalog_orchestrator import (
        match_agent_starter_candidates_to_catalog,
    )

    results = match_agent_starter_candidates_to_catalog(
        goal=AgentStarterGoal.AUTOMATION,
        assessments=[
            deterministic,
            llm_automation,
        ],
        snapshot=snapshot,
    )

    assert [
        result.architecture_id
        for result in results
    ] == [
        "traditional-deterministic-automation",
        "supervised-automation-agent",
    ]

    assert results[0].query_matches == []

    assert len(results[1].query_matches) == 1
    assert [
        entry.identifier
        for entry in results[1].query_matches[0].matched_entries
    ] == [
        "automation-model",
    ]
