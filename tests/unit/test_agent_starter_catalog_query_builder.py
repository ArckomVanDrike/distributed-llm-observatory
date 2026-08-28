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
