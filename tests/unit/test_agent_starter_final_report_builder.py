from datetime import datetime, timezone

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterPlan,
    AgentStarterPreparedInput,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
    ConstraintStrength,
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
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
)


def _context() -> AgentStarterFinalReportContext:
    declared = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    observed = AgentStarterEvidence(
        key="ram_gb",
        source=EvidenceSource.OBSERVED,
        value=16,
    )
    derived = AgentStarterEvidence(
        key="filesystem_write_required",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="The coding workflow modifies files.",
    )
    unknown = AgentStarterEvidence(
        key="gpu_vram_gb",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason="Exact accelerator memory could not be observed.",
    )

    hard = AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[declared],
    )

    soft_evidence = AgentStarterEvidence(
        key="prefer_low_complexity",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    soft = AgentStarterRequirement(
        key="prefer_low_complexity",
        value=True,
        strength=ConstraintStrength.SOFT,
        evidence=[soft_evidence],
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            declared,
            observed,
            derived,
            unknown,
        ],
        requirements=[hard, soft],
    )

    recommended = CandidateArchitectureAssessment(
        architecture_id="local-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The local candidate is technically feasible.",
        ],
        recommendation_reasons=[
            "The local candidate satisfies the evaluated constraints.",
        ],
        supporting_evidence=[
            declared,
            observed,
            derived,
        ],
    )

    rejected = CandidateArchitectureAssessment(
        architecture_id="remote-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The remote candidate is technically feasible.",
        ],
        recommendation_reasons=[
            "The remote candidate violates the local-only constraint.",
        ],
        supporting_evidence=[
            declared,
            observed,
        ],
        blocking_requirements=[hard],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[hard, soft],
        candidate_assessments=[
            recommended,
            rejected,
        ],
    )

    snapshot_id = "catalog-v0-1"

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=plan,
        catalog_snapshot_id=snapshot_id,
        architecture_results=[
            AgentStarterCatalogArchitectureResult(
                architecture_id="local-agent",
                catalog_snapshot_id=snapshot_id,
            ),
            AgentStarterCatalogArchitectureResult(
                architecture_id="remote-agent",
                catalog_snapshot_id=snapshot_id,
            ),
        ],
    )

    resolution = AgentStarterConcreteStackResolution(
        catalog_result=catalog_result,
        stacks=[
            AgentStarterConcreteStack(
                architecture_id="local-agent",
                catalog_snapshot_id=snapshot_id,
            ),
            AgentStarterConcreteStack(
                architecture_id="remote-agent",
                catalog_snapshot_id=snapshot_id,
            ),
        ],
    )

    classification = AgentStarterConcreteStackClassification(
        resolution=resolution,
        recommended_architecture_ids=[
            "local-agent",
        ],
        not_recommended_architecture_ids=[
            "remote-agent",
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

    return AgentStarterFinalReportContext(
        prepared=prepared,
        classification=classification,
        catalog_snapshot=snapshot,
    )


def test_builder_projects_complete_final_report_from_context():
    from observer.core.agent_starter_final_report_builder import (
        build_agent_starter_final_report,
    )

    context = _context()

    report = build_agent_starter_final_report(context)

    assert report.context == context

    assert [
        item.key
        for item in report.declared_evidence
    ] == [
        "source_code_must_stay_local",
    ]
    assert [
        item.key
        for item in report.observed_evidence
    ] == [
        "ram_gb",
    ]
    assert [
        item.key
        for item in report.derived_evidence
    ] == [
        "filesystem_write_required",
    ]
    assert [
        item.key
        for item in report.unknown_evidence
    ] == [
        "gpu_vram_gb",
    ]

    assert [
        item.key
        for item in report.hard_constraints
    ] == [
        "source_code_must_stay_local",
    ]
    assert [
        item.key
        for item in report.soft_preferences
    ] == [
        "prefer_low_complexity",
    ]

    assert [
        explanation.assessment.architecture_id
        for explanation in report.candidate_explanations
    ] == [
        "local-agent",
        "remote-agent",
    ]

    assert report.candidate_explanations[0].why == [
        "The local candidate satisfies the evaluated constraints.",
    ]
    assert report.candidate_explanations[0].why_not == []

    assert report.candidate_explanations[1].why == []
    assert report.candidate_explanations[1].why_not == [
        "The remote candidate violates the local-only constraint.",
    ]

    assert [
        blocker.key
        for blocker in report.blockers
    ] == [
        "source_code_must_stay_local",
    ]

    assert report.upgrade_paths == []


def test_builder_preserves_catalog_freshness_through_context():
    from observer.core.agent_starter_final_report_builder import (
        build_agent_starter_final_report,
    )

    context = _context()

    report = build_agent_starter_final_report(context)

    assert (
        report.context.catalog_snapshot.snapshot_id
        == "catalog-v0-1"
    )
    assert (
        report.context.catalog_snapshot.generated_at
        == datetime(
            2026,
            8,
            29,
            12,
            0,
            tzinfo=timezone.utc,
        )
    )
