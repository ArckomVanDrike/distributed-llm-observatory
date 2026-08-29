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
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[
            "Technical assessment.",
        ],
        recommendation_reasons=[
            "Recommendation assessment.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="classification_fixture_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The fixture records supporting evidence."
                ),
            ),
        ],
    )


def _resolution(
    assessments: list[CandidateArchitectureAssessment],
) -> AgentStarterConcreteStackResolution:
    snapshot_id = "agent-starter-catalog-v0-1"

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        candidate_assessments=assessments,
    )

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=plan,
        catalog_snapshot_id=snapshot_id,
        architecture_results=[
            AgentStarterCatalogArchitectureResult(
                architecture_id=assessment.architecture_id,
                catalog_snapshot_id=snapshot_id,
            )
            for assessment in assessments
        ],
    )

    return AgentStarterConcreteStackResolution(
        catalog_result=catalog_result,
        stacks=[
            AgentStarterConcreteStack(
                architecture_id=assessment.architecture_id,
                catalog_snapshot_id=snapshot_id,
            )
            for assessment in assessments
        ],
    )


def test_classifier_maps_each_verdict_to_matching_bucket():
    from observer.core.agent_starter_concrete_stack_classifier import (
        classify_agent_starter_concrete_stacks,
    )

    resolution = _resolution(
        [
            _assessment(
                "recommended-a",
                RecommendationVerdict.RECOMMENDED,
            ),
            _assessment(
                "possible-a",
                RecommendationVerdict.POSSIBLE,
            ),
            _assessment(
                "possible-not-recommended-a",
                RecommendationVerdict.POSSIBLE_BUT_NOT_RECOMMENDED,
            ),
            _assessment(
                "rejected-a",
                RecommendationVerdict.NOT_RECOMMENDED,
            ),
        ]
    )

    result = classify_agent_starter_concrete_stacks(
        resolution
    )

    assert result.resolution == resolution
    assert result.recommended_architecture_ids == [
        "recommended-a",
    ]
    assert result.possible_architecture_ids == [
        "possible-a",
    ]
    assert (
        result.possible_but_not_recommended_architecture_ids
        == [
            "possible-not-recommended-a",
        ]
    )
    assert result.not_recommended_architecture_ids == [
        "rejected-a",
    ]


def test_classifier_preserves_multiple_recommended_architectures():
    from observer.core.agent_starter_concrete_stack_classifier import (
        classify_agent_starter_concrete_stacks,
    )

    resolution = _resolution(
        [
            _assessment(
                "recommended-a",
                RecommendationVerdict.RECOMMENDED,
            ),
            _assessment(
                "recommended-b",
                RecommendationVerdict.RECOMMENDED,
            ),
        ]
    )

    result = classify_agent_starter_concrete_stacks(
        resolution
    )

    assert result.recommended_architecture_ids == [
        "recommended-a",
        "recommended-b",
    ]
    assert result.possible_architecture_ids == []
    assert (
        result.possible_but_not_recommended_architecture_ids
        == []
    )
    assert result.not_recommended_architecture_ids == []


def test_classifier_preserves_candidate_order_within_each_bucket():
    from observer.core.agent_starter_concrete_stack_classifier import (
        classify_agent_starter_concrete_stacks,
    )

    resolution = _resolution(
        [
            _assessment(
                "possible-a",
                RecommendationVerdict.POSSIBLE,
            ),
            _assessment(
                "recommended-a",
                RecommendationVerdict.RECOMMENDED,
            ),
            _assessment(
                "possible-b",
                RecommendationVerdict.POSSIBLE,
            ),
            _assessment(
                "recommended-b",
                RecommendationVerdict.RECOMMENDED,
            ),
        ]
    )

    result = classify_agent_starter_concrete_stacks(
        resolution
    )

    assert result.recommended_architecture_ids == [
        "recommended-a",
        "recommended-b",
    ]
    assert result.possible_architecture_ids == [
        "possible-a",
        "possible-b",
    ]
