import pytest
from pydantic import ValidationError

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
                    "The fixture records decision evidence "
                    "required by the candidate assessment contract."
                ),
            ),
        ],
    )


def _resolution() -> AgentStarterConcreteStackResolution:
    assessments = [
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

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        candidate_assessments=assessments,
    )

    snapshot_id = "agent-starter-catalog-v0-1"

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


def test_stack_classification_records_all_verdict_groups():
    from schemas.agent_starter_result import (
        AgentStarterConcreteStackClassification,
    )

    resolution = _resolution()

    classification = AgentStarterConcreteStackClassification(
        resolution=resolution,
        recommended_architecture_ids=[
            "recommended-a",
        ],
        possible_architecture_ids=[
            "possible-a",
        ],
        possible_but_not_recommended_architecture_ids=[
            "possible-not-recommended-a",
        ],
        not_recommended_architecture_ids=[
            "rejected-a",
        ],
    )

    assert classification.resolution == resolution
    assert classification.recommended_architecture_ids == [
        "recommended-a",
    ]
    assert classification.possible_architecture_ids == [
        "possible-a",
    ]
    assert (
        classification.possible_but_not_recommended_architecture_ids
        == [
            "possible-not-recommended-a",
        ]
    )
    assert classification.not_recommended_architecture_ids == [
        "rejected-a",
    ]


def test_stack_classification_allows_multiple_recommended_architectures():
    from schemas.agent_starter_result import (
        AgentStarterConcreteStackClassification,
    )

    resolution = _resolution()

    # Contract deliberately permits plurality.
    classification = AgentStarterConcreteStackClassification(
        resolution=resolution,
        recommended_architecture_ids=[
            "recommended-a",
            "possible-a",
        ],
        possible_but_not_recommended_architecture_ids=[
            "possible-not-recommended-a",
        ],
        not_recommended_architecture_ids=[
            "rejected-a",
        ],
    )

    assert classification.recommended_architecture_ids == [
        "recommended-a",
        "possible-a",
    ]


def test_stack_classification_rejects_duplicate_architecture_membership():
    from schemas.agent_starter_result import (
        AgentStarterConcreteStackClassification,
    )

    resolution = _resolution()

    with pytest.raises(
        ValidationError,
        match="exactly once",
    ):
        AgentStarterConcreteStackClassification(
            resolution=resolution,
            recommended_architecture_ids=[
                "recommended-a",
            ],
            possible_architecture_ids=[
                "recommended-a",
                "possible-a",
            ],
            possible_but_not_recommended_architecture_ids=[
                "possible-not-recommended-a",
            ],
            not_recommended_architecture_ids=[
                "rejected-a",
            ],
        )


def test_stack_classification_rejects_missing_architecture():
    from schemas.agent_starter_result import (
        AgentStarterConcreteStackClassification,
    )

    resolution = _resolution()

    with pytest.raises(
        ValidationError,
        match="exactly once",
    ):
        AgentStarterConcreteStackClassification(
            resolution=resolution,
            recommended_architecture_ids=[
                "recommended-a",
            ],
            possible_architecture_ids=[
                "possible-a",
            ],
            possible_but_not_recommended_architecture_ids=[
                "possible-not-recommended-a",
            ],
        )
