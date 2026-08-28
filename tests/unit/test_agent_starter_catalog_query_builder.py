from observer.core.agent_starter_catalog_query_builder import (
    build_agent_starter_catalog_queries,
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
)


def test_catalog_query_builder_maps_coding_assessment_to_llm_query():
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
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
    )

    assert len(queries) == 1

    query = queries[0]

    assert (
        query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query.required_capabilities == ["coding"]

    # Local processing evidence is not equivalent to
    # a concrete on-device deployment mode.
    assert query.required_deployment_modes == []

    # These properties have not been established by evidence.
    assert query.required_runtime is None
    assert query.required_pricing_class is None


def test_catalog_query_builder_returns_no_llm_query_for_deterministic_automation():
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

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.AUTOMATION,
        assessment=assessment,
    )

    assert queries == []


def test_catalog_query_builder_returns_llm_query_for_llm_automation():
    assessment = CandidateArchitectureAssessment(
        architecture_id="supervised-automation-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The automation architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The automation architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The automation architecture uses an LLM."
                ),
            ),
        ],
    )

    queries = build_agent_starter_catalog_queries(
        goal=AgentStarterGoal.AUTOMATION,
        assessment=assessment,
    )

    assert len(queries) == 1

    query = queries[0]

    assert (
        query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query.required_capabilities == []
    assert query.required_deployment_modes == []
    assert query.required_runtime is None
    assert query.required_pricing_class is None


def test_catalog_query_builder_rejects_automation_without_llm_usage_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="unknown-automation",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "LLM usage is not established.",
        ],
        recommendation_reasons=[
            "The architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="unrelated_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Unrelated evidence.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Automation catalog mapping requires exactly one "
            "candidate_uses_llm evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.AUTOMATION,
            assessment=assessment,
        )


def test_catalog_query_builder_rejects_conflicting_automation_llm_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="conflicting-automation",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "The automation LLM usage evidence conflicts.",
        ],
        recommendation_reasons=[
            "The architecture cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="The candidate does not use an LLM.",
            ),
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate uses an LLM.",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Automation catalog mapping requires exactly one "
            "candidate_uses_llm evidence value"
        ),
    ):
        build_agent_starter_catalog_queries(
            goal=AgentStarterGoal.AUTOMATION,
            assessment=assessment,
        )
