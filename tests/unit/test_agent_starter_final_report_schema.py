from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

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
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
    AgentStarterConcreteStackClassification,
    AgentStarterConcreteStackResolution,
)
from schemas.agent_starter_stack import AgentStarterConcreteStack


def _fixture():
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
        reason="The requested coding workflow modifies files.",
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
    soft = AgentStarterRequirement(
        key="prefer_low_complexity",
        value=True,
        strength=ConstraintStrength.SOFT,
        evidence=[
            AgentStarterEvidence(
                key="prefer_low_complexity",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
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

    assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The candidate is technically feasible.",
        ],
        recommendation_reasons=[
            "The local architecture satisfies the evaluated constraints.",
        ],
        supporting_evidence=[
            declared,
            observed,
            derived,
        ],
    )

    snapshot_id = "catalog-v0-1"

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=AgentStarterPlan(
            goal=AgentStarterGoal.CODING,
            requirements=[hard, soft],
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

    stack = AgentStarterConcreteStack(
        architecture_id="local-coding-agent",
        catalog_snapshot_id=snapshot_id,
    )

    resolution = AgentStarterConcreteStackResolution(
        catalog_result=catalog_result,
        stacks=[stack],
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

    return {
        "prepared": prepared,
        "classification": classification,
        "snapshot": snapshot,
        "assessment": assessment,
        "stack": stack,
        "declared": declared,
        "observed": observed,
        "derived": derived,
        "unknown": unknown,
        "hard": hard,
        "soft": soft,
    }


def test_final_report_accepts_exact_source_projections():
    from schemas.agent_starter_report import (
        AgentStarterCandidateExplanation,
        AgentStarterFinalReport,
        AgentStarterFinalReportContext,
    )

    fixture = _fixture()

    context = AgentStarterFinalReportContext(
        prepared=fixture["prepared"],
        classification=fixture["classification"],
        catalog_snapshot=fixture["snapshot"],
    )

    explanation = AgentStarterCandidateExplanation(
        assessment=fixture["assessment"],
        concrete_stack=fixture["stack"],
        why=fixture["assessment"].recommendation_reasons,
        why_not=[],
    )

    report = AgentStarterFinalReport(
        context=context,
        candidate_explanations=[explanation],
        observed_evidence=[fixture["observed"]],
        declared_evidence=[fixture["declared"]],
        derived_evidence=[fixture["derived"]],
        unknown_evidence=[fixture["unknown"]],
        hard_constraints=[fixture["hard"]],
        soft_preferences=[fixture["soft"]],
        blockers=[],
        upgrade_paths=[],
    )

    assert report.context == context
    assert report.candidate_explanations == [explanation]
    assert report.observed_evidence == [fixture["observed"]]
    assert report.declared_evidence == [fixture["declared"]]
    assert report.derived_evidence == [fixture["derived"]]
    assert report.unknown_evidence == [fixture["unknown"]]
    assert report.hard_constraints == [fixture["hard"]]
    assert report.soft_preferences == [fixture["soft"]]


def test_final_report_rejects_invented_evidence():
    from schemas.agent_starter_report import (
        AgentStarterCandidateExplanation,
        AgentStarterFinalReport,
        AgentStarterFinalReportContext,
    )

    fixture = _fixture()

    context = AgentStarterFinalReportContext(
        prepared=fixture["prepared"],
        classification=fixture["classification"],
        catalog_snapshot=fixture["snapshot"],
    )

    explanation = AgentStarterCandidateExplanation(
        assessment=fixture["assessment"],
        concrete_stack=fixture["stack"],
        why=fixture["assessment"].recommendation_reasons,
        why_not=[],
    )

    invented = AgentStarterEvidence(
        key="invented",
        source=EvidenceSource.OBSERVED,
        value=True,
    )

    with pytest.raises(
        ValidationError,
        match="evidence projection",
    ):
        AgentStarterFinalReport(
            context=context,
            candidate_explanations=[explanation],
            observed_evidence=[
                fixture["observed"],
                invented,
            ],
            declared_evidence=[fixture["declared"]],
            derived_evidence=[fixture["derived"]],
            unknown_evidence=[fixture["unknown"]],
            hard_constraints=[fixture["hard"]],
            soft_preferences=[fixture["soft"]],
            blockers=[],
            upgrade_paths=[],
        )


def test_final_report_rejects_missing_candidate_explanation():
    from schemas.agent_starter_report import (
        AgentStarterFinalReport,
        AgentStarterFinalReportContext,
    )

    fixture = _fixture()

    context = AgentStarterFinalReportContext(
        prepared=fixture["prepared"],
        classification=fixture["classification"],
        catalog_snapshot=fixture["snapshot"],
    )

    with pytest.raises(
        ValidationError,
        match="candidate explanation",
    ):
        AgentStarterFinalReport(
            context=context,
            candidate_explanations=[],
            observed_evidence=[fixture["observed"]],
            declared_evidence=[fixture["declared"]],
            derived_evidence=[fixture["derived"]],
            unknown_evidence=[fixture["unknown"]],
            hard_constraints=[fixture["hard"]],
            soft_preferences=[fixture["soft"]],
            blockers=[],
            upgrade_paths=[],
        )


def test_final_report_rejects_invented_upgrade_path():
    from schemas.agent_starter_report import (
        AgentStarterCandidateExplanation,
        AgentStarterFinalReport,
        AgentStarterFinalReportContext,
    )

    fixture = _fixture()

    context = AgentStarterFinalReportContext(
        prepared=fixture["prepared"],
        classification=fixture["classification"],
        catalog_snapshot=fixture["snapshot"],
    )

    explanation = AgentStarterCandidateExplanation(
        assessment=fixture["assessment"],
        concrete_stack=fixture["stack"],
        why=fixture["assessment"].recommendation_reasons,
        why_not=[],
    )

    with pytest.raises(
        ValidationError,
        match="upgrade path",
    ):
        AgentStarterFinalReport(
            context=context,
            candidate_explanations=[explanation],
            observed_evidence=[fixture["observed"]],
            declared_evidence=[fixture["declared"]],
            derived_evidence=[fixture["derived"]],
            unknown_evidence=[fixture["unknown"]],
            hard_constraints=[fixture["hard"]],
            soft_preferences=[fixture["soft"]],
            blockers=[],
            upgrade_paths=[
                "Buy a larger GPU.",
            ],
        )
