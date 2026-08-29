from datetime import datetime, timezone

from observer.core.agent_starter_final_report_builder import (
    build_agent_starter_final_report,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterPlan,
    AgentStarterPreparedInput,
    CandidateArchitectureAssessment,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogArchitectureResult,
    AgentStarterCatalogSnapshot,
)
from schemas.agent_starter_report import (
    AgentStarterFinalReportContext,
)
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
    AgentStarterConcreteStackClassification,
    AgentStarterConcreteStackResolution,
)
from schemas.agent_starter_stack import AgentStarterConcreteStack


def _assessment(
    architecture_id: str,
    verdict: RecommendationVerdict,
) -> CandidateArchitectureAssessment:
    evidence = AgentStarterEvidence(
        key="fixture",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Fixture evidence.",
    )

    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=verdict,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=["Technically feasible."],
        recommendation_reasons=["Recorded recommendation reason."],
        supporting_evidence=[evidence],
    )


def test_final_report_exposes_recommendation_groups_and_stacks():
    assessments = [
        _assessment(
            "recommended-a",
            RecommendationVerdict.RECOMMENDED,
        ),
        _assessment(
            "recommended-b",
            RecommendationVerdict.RECOMMENDED,
        ),
        _assessment(
            "alternative-a",
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

    snapshot_id = "catalog-v0-1"

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=AgentStarterPlan(
            goal=AgentStarterGoal.CODING,
            candidate_assessments=assessments,
        ),
        catalog_snapshot_id=snapshot_id,
        architecture_results=[
            AgentStarterCatalogArchitectureResult(
                architecture_id=item.architecture_id,
                catalog_snapshot_id=snapshot_id,
            )
            for item in assessments
        ],
    )

    stacks = [
        AgentStarterConcreteStack(
            architecture_id=item.architecture_id,
            catalog_snapshot_id=snapshot_id,
        )
        for item in assessments
    ]

    classification = AgentStarterConcreteStackClassification(
        resolution=AgentStarterConcreteStackResolution(
            catalog_result=catalog_result,
            stacks=stacks,
        ),
        recommended_architecture_ids=[
            "recommended-a",
            "recommended-b",
        ],
        possible_architecture_ids=[
            "alternative-a",
        ],
        possible_but_not_recommended_architecture_ids=[
            "possible-not-recommended-a",
        ],
        not_recommended_architecture_ids=[
            "rejected-a",
        ],
    )

    context = AgentStarterFinalReportContext(
        prepared=AgentStarterPreparedInput(
            goal=AgentStarterGoal.CODING,
        ),
        classification=classification,
        catalog_snapshot=AgentStarterCatalogSnapshot(
            snapshot_id=snapshot_id,
            generated_at=datetime(
                2026,
                8,
                29,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        ),
    )

    report = build_agent_starter_final_report(context)

    assert report.recommended_architecture_ids == [
        "recommended-a",
        "recommended-b",
    ]
    assert [
        stack.architecture_id
        for stack in report.recommended_stacks
    ] == [
        "recommended-a",
        "recommended-b",
    ]

    assert report.alternative_architecture_ids == [
        "alternative-a",
    ]
    assert [
        stack.architecture_id
        for stack in report.alternative_stacks
    ] == [
        "alternative-a",
    ]

    assert (
        report.possible_but_not_recommended_architecture_ids
        == [
            "possible-not-recommended-a",
        ]
    )

    assert report.not_recommended_architecture_ids == [
        "rejected-a",
    ]
