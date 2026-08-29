from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

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


def _assessment(
    architecture_id: str,
) -> CandidateArchitectureAssessment:
    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The candidate is technically feasible.",
        ],
        recommendation_reasons=[
            "The candidate is recommended.",
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


def _classification(
    *,
    goal: AgentStarterGoal = AgentStarterGoal.CODING,
    snapshot_id: str = "catalog-v0-1",
) -> AgentStarterConcreteStackClassification:
    assessment = _assessment("local-agent")

    catalog_result = AgentStarterCatalogMatchingResult(
        plan=AgentStarterPlan(
            goal=goal,
            candidate_assessments=[assessment],
        ),
        catalog_snapshot_id=snapshot_id,
        architecture_results=[
            AgentStarterCatalogArchitectureResult(
                architecture_id="local-agent",
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
        ],
    )

    return AgentStarterConcreteStackClassification(
        resolution=resolution,
        recommended_architecture_ids=[
            "local-agent",
        ],
    )


def _snapshot(
    snapshot_id: str = "catalog-v0-1",
) -> AgentStarterCatalogSnapshot:
    return AgentStarterCatalogSnapshot(
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


def test_final_report_context_preserves_prepared_input_and_snapshot():
    from schemas.agent_starter_report import (
        AgentStarterFinalReportContext,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    classification = _classification()
    snapshot = _snapshot()

    context = AgentStarterFinalReportContext(
        prepared=prepared,
        classification=classification,
        catalog_snapshot=snapshot,
    )

    assert context.prepared == prepared
    assert context.classification == classification
    assert context.catalog_snapshot == snapshot


def test_final_report_context_rejects_goal_mismatch():
    from schemas.agent_starter_report import (
        AgentStarterFinalReportContext,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.VOICE,
    )

    with pytest.raises(
        ValidationError,
        match="goal",
    ):
        AgentStarterFinalReportContext(
            prepared=prepared,
            classification=_classification(
                goal=AgentStarterGoal.CODING,
            ),
            catalog_snapshot=_snapshot(),
        )


def test_final_report_context_rejects_snapshot_mismatch():
    from schemas.agent_starter_report import (
        AgentStarterFinalReportContext,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    with pytest.raises(
        ValidationError,
        match="snapshot",
    ):
        AgentStarterFinalReportContext(
            prepared=prepared,
            classification=_classification(
                snapshot_id="catalog-a",
            ),
            catalog_snapshot=_snapshot(
                snapshot_id="catalog-b",
            ),
        )
