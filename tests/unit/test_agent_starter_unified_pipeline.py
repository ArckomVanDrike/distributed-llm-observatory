from datetime import datetime, timezone

from observer.core.agent_starter_assessment_orchestrator import (
    assess_agent_starter_candidates,
)
from observer.core.agent_starter_catalog_pipeline import (
    run_agent_starter_catalog_matching,
)
from observer.core.agent_starter_concrete_stack_pipeline import (
    run_agent_starter_concrete_stack_pipeline,
)
from observer.core.agent_starter_final_report_pipeline import (
    run_agent_starter_final_report_pipeline,
)
from observer.core.agent_starter_input_orchestrator import (
    prepare_agent_starter_input,
)
from observer.core.agent_starter_plan_builder import (
    build_agent_starter_plan,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    EvidenceSource,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogSnapshot,
)


def test_unified_pipeline_matches_explicit_stage_composition():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-unified-test",
        generated_at=datetime(
            2026,
            8,
            29,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        entries=[],
    )

    prepared = prepare_agent_starter_input(intake)

    assessments = assess_agent_starter_candidates(
        prepared=prepared,
    )

    plan = build_agent_starter_plan(
        goal=prepared.goal,
        requirements=list(prepared.requirements),
        candidate_assessments=assessments,
    )

    catalog_result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    classification = (
        run_agent_starter_concrete_stack_pipeline(
            catalog_result
        )
    )

    expected = run_agent_starter_final_report_pipeline(
        prepared=prepared,
        classification=classification,
        catalog_snapshot=snapshot,
    )

    from observer.core.agent_starter_unified_pipeline import (
        run_agent_starter_unified_pipeline,
    )

    actual = run_agent_starter_unified_pipeline(
        intake=intake,
        catalog_snapshot=snapshot,
    )

    assert actual == expected

    assert actual.context.prepared == prepared
    assert actual.context.catalog_snapshot == snapshot

    derived = {
        evidence.key: evidence.value
        for evidence in actual.derived_evidence
    }

    assert (
        derived["semantic_interpretation_required"]
        is False
    )


def test_unified_pipeline_preserves_explicit_catalog_provenance():
    from observer.core.agent_starter_unified_pipeline import (
        run_agent_starter_unified_pipeline,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="explicit-catalog-snapshot",
        generated_at=datetime(
            2026,
            8,
            29,
            13,
            0,
            tzinfo=timezone.utc,
        ),
        entries=[],
    )

    report = run_agent_starter_unified_pipeline(
        intake=intake,
        catalog_snapshot=snapshot,
    )

    assert (
        report.context.catalog_snapshot.snapshot_id
        == "explicit-catalog-snapshot"
    )
    assert (
        report.context
        .classification
        .resolution
        .catalog_result
        .catalog_snapshot_id
        == "explicit-catalog-snapshot"
    )


def test_unified_pipeline_forwards_explicit_compatibility(
    monkeypatch,
):
    import observer.core.agent_starter_unified_pipeline as pipeline_module

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-compatibility-test",
        generated_at=datetime(
            2026,
            8,
            29,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        entries=[],
    )

    explicit_compatibility = {}

    original_assess = (
        pipeline_module.assess_agent_starter_candidates
    )
    captured = {}

    def capturing_assess(
        *,
        prepared,
        compatibility_by_architecture=None,
    ):
        captured["compatibility"] = (
            compatibility_by_architecture
        )

        return original_assess(
            prepared=prepared,
            compatibility_by_architecture=(
                compatibility_by_architecture
            ),
        )

    monkeypatch.setattr(
        pipeline_module,
        "assess_agent_starter_candidates",
        capturing_assess,
    )

    report = pipeline_module.run_agent_starter_unified_pipeline(
        intake=intake,
        catalog_snapshot=snapshot,
        compatibility_by_architecture=explicit_compatibility,
    )

    assert (
        captured["compatibility"]
        is explicit_compatibility
    )
    assert report.context.prepared.goal is AgentStarterGoal.AUTOMATION
