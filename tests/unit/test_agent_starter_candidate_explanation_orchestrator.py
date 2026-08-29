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
    AgentStarterConcreteStackClassification,
    AgentStarterConcreteStackResolution,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
)


def _assessment(
    architecture_id: str,
    verdict: RecommendationVerdict,
) -> CandidateArchitectureAssessment:
    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=verdict,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The candidate is technically feasible.",
        ],
        recommendation_reasons=[
            f"Decision reason for {architecture_id}.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="fixture_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Fixture evidence supports the assessment.",
            ),
        ],
    )


def _classification() -> AgentStarterConcreteStackClassification:
    assessments = [
        _assessment(
            "recommended-agent",
            RecommendationVerdict.RECOMMENDED,
        ),
        _assessment(
            "rejected-agent",
            RecommendationVerdict.NOT_RECOMMENDED,
        ),
        _assessment(
            "possible-agent",
            RecommendationVerdict.POSSIBLE,
        ),
    ]

    snapshot_id = "catalog-v0-1"

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=AgentStarterPlan(
            goal=AgentStarterGoal.CODING,
            candidate_assessments=assessments,
        ),
        catalog_snapshot_id=snapshot_id,
        architecture_results=[
            AgentStarterCatalogArchitectureResult(
                architecture_id=assessment.architecture_id,
                catalog_snapshot_id=snapshot_id,
            )
            for assessment in assessments
        ],
    )

    resolution = AgentStarterConcreteStackResolution(
        catalog_result=catalog_result,
        stacks=[
            AgentStarterConcreteStack(
                architecture_id=assessment.architecture_id,
                catalog_snapshot_id=snapshot_id,
            )
            for assessment in assessments
        ],
    )

    return AgentStarterConcreteStackClassification(
        resolution=resolution,
        recommended_architecture_ids=[
            "recommended-agent",
        ],
        possible_architecture_ids=[
            "possible-agent",
        ],
        not_recommended_architecture_ids=[
            "rejected-agent",
        ],
    )


def test_orchestrator_builds_explanations_for_all_candidates_in_plan_order():
    from observer.core.agent_starter_candidate_explanation_orchestrator import (
        build_agent_starter_candidate_explanations,
    )

    classification = _classification()

    result = build_agent_starter_candidate_explanations(
        classification
    )

    assert [
        explanation.assessment.architecture_id
        for explanation in result
    ] == [
        "recommended-agent",
        "rejected-agent",
        "possible-agent",
    ]

    assert [
        explanation.concrete_stack.architecture_id
        for explanation in result
    ] == [
        "recommended-agent",
        "rejected-agent",
        "possible-agent",
    ]


def test_orchestrator_preserves_why_and_why_not_without_filtering():
    from observer.core.agent_starter_candidate_explanation_orchestrator import (
        build_agent_starter_candidate_explanations,
    )

    classification = _classification()

    recommended, rejected, possible = (
        build_agent_starter_candidate_explanations(
            classification
        )
    )

    assert recommended.why == [
        "Decision reason for recommended-agent.",
    ]
    assert recommended.why_not == []

    assert rejected.why == []
    assert rejected.why_not == [
        "Decision reason for rejected-agent.",
    ]

    assert possible.why == [
        "Decision reason for possible-agent.",
    ]
    assert possible.why_not == []
