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
)
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
)


def test_catalog_matching_result_records_plan_and_catalog_results():
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

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=[assessment],
    )

    catalog_result = AgentStarterCatalogArchitectureResult(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="catalog-2026-08-28",
        query_matches=[],
    )

    result = AgentStarterCatalogMatchingResult(
        plan=plan,
        catalog_snapshot_id="catalog-2026-08-28",
        architecture_results=[catalog_result],
    )

    assert result.plan == plan
    assert result.catalog_snapshot_id == "catalog-2026-08-28"
    assert result.architecture_results == [catalog_result]


def test_catalog_matching_result_rejects_reordered_architecture_results():
    import pytest
    from pydantic import ValidationError

    first_assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=["First architecture is feasible."],
        recommendation_reasons=["First architecture is recommended."],
        supporting_evidence=[
            AgentStarterEvidence(
                key="first_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="First architecture evidence.",
            ),
        ],
    )

    second_assessment = CandidateArchitectureAssessment(
        architecture_id="remote-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=["Second architecture is feasible."],
        recommendation_reasons=["Second architecture is possible."],
        supporting_evidence=[
            AgentStarterEvidence(
                key="second_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Second architecture evidence.",
            ),
        ],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=[
            first_assessment,
            second_assessment,
        ],
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Catalog architecture results must correspond exactly "
            "and in order to plan candidate assessments"
        ),
    ):
        AgentStarterCatalogMatchingResult(
            plan=plan,
            catalog_snapshot_id="catalog-2026-08-28",
            architecture_results=[
                AgentStarterCatalogArchitectureResult(
                    architecture_id="remote-coding-agent",
                    catalog_snapshot_id="catalog-2026-08-28",
                    query_matches=[],
                ),
                AgentStarterCatalogArchitectureResult(
                    architecture_id="local-coding-agent",
                    catalog_snapshot_id="catalog-2026-08-28",
                    query_matches=[],
                ),
            ],
        )


def test_catalog_matching_result_rejects_architecture_result_from_other_snapshot():
    import pytest
    from pydantic import ValidationError

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

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=[assessment],
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Catalog architecture results must come from "
            "the declared catalog snapshot"
        ),
    ):
        AgentStarterCatalogMatchingResult(
            plan=plan,
            catalog_snapshot_id="catalog-current",
            architecture_results=[
                AgentStarterCatalogArchitectureResult(
                    architecture_id="local-coding-agent",
                    catalog_snapshot_id="catalog-old",
                    query_matches=[],
                ),
            ],
        )
