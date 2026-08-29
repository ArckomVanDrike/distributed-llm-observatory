from observer.core.agent_starter_input_orchestrator import (
    prepare_agent_starter_input,
)
from observer.core.agent_starter_technical_requirement_orchestrator import (
    extract_agent_starter_requested_capabilities,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    EvidenceSource,
)


def test_requested_capabilities_project_only_assessable_true_capabilities():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="document_input_includes_scanned_pages",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="user_requires_citations",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    prepared = prepare_agent_starter_input(intake)

    capabilities = extract_agent_starter_requested_capabilities(
        prepared
    )

    assert [
        capability.key
        for capability in capabilities
    ] == [
        "ocr_required",
        "source_provenance_required",
    ]

    assert all(
        capability.source is EvidenceSource.DERIVED
        for capability in capabilities
    )
    assert all(
        capability.value is True
        for capability in capabilities
    )

    assert "documents_include_scans" not in {
        capability.key
        for capability in capabilities
    }
    assert "citations_required" not in {
        capability.key
        for capability in capabilities
    }


def test_requested_capabilities_preserve_prepared_evidence_objects():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="run_tests",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    prepared = prepare_agent_starter_input(intake)

    capabilities = extract_agent_starter_requested_capabilities(
        prepared
    )

    assert [
        capability.key
        for capability in capabilities
    ] == [
        "filesystem_read",
        "filesystem_write",
        "shell_execution",
        "test_execution",
    ]

    for capability in capabilities:
        assert capability in prepared.evidence


def test_final_report_exposes_exact_requested_capabilities():
    from datetime import datetime, timezone

    from observer.core.agent_starter_unified_pipeline import (
        run_agent_starter_unified_pipeline,
    )
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogSnapshot,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="run_tests",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="requested-capabilities-test",
        generated_at=datetime(
            2026,
            8,
            29,
            16,
            0,
            tzinfo=timezone.utc,
        ),
        entries=[],
    )

    report = run_agent_starter_unified_pipeline(
        intake=intake,
        catalog_snapshot=snapshot,
    )

    expected = extract_agent_starter_requested_capabilities(
        report.context.prepared
    )

    assert report.requested_capabilities == expected
    assert [
        capability.key
        for capability in report.requested_capabilities
    ] == [
        "filesystem_read",
        "filesystem_write",
        "shell_execution",
        "test_execution",
    ]
