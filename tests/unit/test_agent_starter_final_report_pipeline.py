from datetime import datetime, timezone

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
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
    AgentStarterConcreteStackClassification,
    AgentStarterConcreteStackResolution,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
)


def test_final_report_pipeline_builds_report_from_source_objects():
    from observer.core.agent_starter_final_report_pipeline import (
        run_agent_starter_final_report_pipeline,
    )

    evidence = AgentStarterEvidence(
        key="filesystem_write_required",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="The requested coding workflow modifies files.",
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[evidence],
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The candidate is technically feasible.",
        ],
        recommendation_reasons=[
            "The candidate satisfies the evaluated constraints.",
        ],
        supporting_evidence=[evidence],
    )

    snapshot_id = "catalog-v0-1"

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=AgentStarterPlan(
            goal=AgentStarterGoal.CODING,
            candidate_assessments=[assessment],
        ),
        catalog_snapshot_id=snapshot_id,
        architecture_results=[
            AgentStarterCatalogArchitectureResult(
                architecture_id="local-coding-agent",
                catalog_snapshot_id=snapshot_id,
            ),
        ],
    )

    resolution = AgentStarterConcreteStackResolution(
        catalog_result=catalog_result,
        stacks=[
            AgentStarterConcreteStack(
                architecture_id="local-coding-agent",
                catalog_snapshot_id=snapshot_id,
            ),
        ],
    )

    classification = AgentStarterConcreteStackClassification(
        resolution=resolution,
        recommended_architecture_ids=[
            "local-coding-agent",
        ],
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id=snapshot_id,
        generated_at=datetime(
            2026,
            8,
            29,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    report = run_agent_starter_final_report_pipeline(
        prepared=prepared,
        classification=classification,
        catalog_snapshot=snapshot,
    )

    assert report.context.prepared == prepared
    assert report.context.classification == classification
    assert report.context.catalog_snapshot == snapshot

    assert report.derived_evidence == [evidence]

    assert len(report.candidate_explanations) == 1

    explanation = report.candidate_explanations[0]

    assert (
        explanation.assessment.architecture_id
        == "local-coding-agent"
    )
    assert explanation.why == [
        "The candidate satisfies the evaluated constraints.",
    ]
    assert explanation.why_not == []

    assert report.blockers == []
    assert report.upgrade_paths == []
