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
