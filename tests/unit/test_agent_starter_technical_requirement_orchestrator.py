from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    AgentStarterPreparedInput,
    EvidenceSource,
    TechnicalRequirementStatus,
)


def _prepared_with_filesystem_write() -> AgentStarterPreparedInput:
    return AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="filesystem_write",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "Code modification requires filesystem write."
                ),
            ),
        ],
    )


def test_builds_satisfied_filesystem_write_assessment():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    support = AgentStarterEvidence(
        key="candidate_supports_filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Candidate provides filesystem write.",
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
        evidence=[support],
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=_prepared_with_filesystem_write(),
            candidate=candidate,
        )
    )

    assert len(assessments) == 1
    assert assessments[0].key == "filesystem_write"
    assert (
        assessments[0].status
        is TechnicalRequirementStatus.SATISFIED
    )
    assert assessments[0].supporting_evidence == [support]


def test_builds_unsatisfied_filesystem_write_assessment():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    lack = AgentStarterEvidence(
        key="candidate_supports_filesystem_write",
        source=EvidenceSource.DERIVED,
        value=False,
        reason="Candidate cannot write files.",
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="restricted-coding-agent",
        goal=AgentStarterGoal.CODING,
        evidence=[lack],
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=_prepared_with_filesystem_write(),
            candidate=candidate,
        )
    )

    assert len(assessments) == 1
    assert (
        assessments[0].status
        is TechnicalRequirementStatus.UNSATISFIED
    )
    assert assessments[0].supporting_evidence == [lack]


def test_missing_candidate_support_remains_unknown():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="unknown-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=_prepared_with_filesystem_write(),
            candidate=candidate,
        )
    )

    assert len(assessments) == 1
    assert (
        assessments[0].status
        is TechnicalRequirementStatus.UNKNOWN
    )


def test_unmapped_derived_capability_is_not_silently_inferred():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="container_isolation",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Autonomous execution may require isolation.",
            ),
        ],
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assert (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
        == []
    )

def test_declared_evidence_is_not_reinterpreted_as_derived_capability():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="filesystem_write",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assert (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
        == []
    )


def test_false_derived_capability_is_not_treated_as_required():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="filesystem_write",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="Filesystem write is not required.",
            ),
        ],
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assert (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
        == []
    )


def test_builds_requirement_from_real_prepared_capability_evidence():
    from observer.core.agent_starter_input_orchestrator import (
        prepare_agent_starter_input,
    )
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    prepared = prepare_agent_starter_input(intake)

    lack = AgentStarterEvidence(
        key="candidate_supports_filesystem_write",
        source=EvidenceSource.DERIVED,
        value=False,
        reason="Candidate cannot write files.",
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="restricted-coding-agent",
        goal=AgentStarterGoal.CODING,
        evidence=[lack],
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
    )

    filesystem_write = [
        assessment
        for assessment in assessments
        if assessment.key == "filesystem_write"
    ]

    assert len(filesystem_write) == 1
    assert (
        filesystem_write[0].status
        is TechnicalRequirementStatus.UNSATISFIED
    )
    assert filesystem_write[0].supporting_evidence == [lack]


def test_maps_filesystem_read_capability_to_candidate_evidence():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="filesystem_read",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "Repository access requires filesystem read."
                ),
            ),
        ],
    )

    support = AgentStarterEvidence(
        key="candidate_supports_filesystem_read",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Candidate provides filesystem read.",
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
        evidence=[support],
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
    )

    assert len(assessments) == 1
    assert assessments[0].key == "filesystem_read"
    assert (
        assessments[0].status
        is TechnicalRequirementStatus.SATISFIED
    )
    assert assessments[0].supporting_evidence == [support]


def test_real_modify_files_intent_assesses_both_filesystem_capabilities():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from observer.core.agent_starter_input_orchestrator import (
        prepare_agent_starter_input,
    )
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    prepared = prepare_agent_starter_input(intake)

    local_candidate, _ = generate_agent_starter_candidates(
        prepared
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=local_candidate,
        )
    )

    assert [
        assessment.key
        for assessment in assessments
    ] == [
        "filesystem_read",
        "filesystem_write",
    ]

    assert all(
        assessment.status
        is TechnicalRequirementStatus.SATISFIED
        for assessment in assessments
    )


def test_maps_shell_execution_capability_to_candidate_evidence():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="shell_execution",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Running tests requires shell execution.",
            ),
        ],
    )

    support = AgentStarterEvidence(
        key="candidate_supports_shell_execution",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Candidate provides shell execution.",
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
        evidence=[support],
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
    )

    assert len(assessments) == 1
    assert assessments[0].key == "shell_execution"
    assert (
        assessments[0].status
        is TechnicalRequirementStatus.SATISFIED
    )
    assert assessments[0].supporting_evidence == [support]


def test_real_run_tests_intent_assesses_shell_and_test_execution():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from observer.core.agent_starter_input_orchestrator import (
        prepare_agent_starter_input,
    )
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="run_tests",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    prepared = prepare_agent_starter_input(intake)

    local_candidate, _ = generate_agent_starter_candidates(
        prepared
    )

    assert [
        evidence.key
        for evidence in prepared.evidence
    ] == [
        "run_tests",
        "shell_execution",
        "test_execution",
    ]

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=local_candidate,
        )
    )

    assert [
        assessment.key
        for assessment in assessments
    ] == [
        "shell_execution",
        "test_execution",
    ]

    assert all(
        assessment.status
        is TechnicalRequirementStatus.SATISFIED
        for assessment in assessments
    )

def test_maps_test_execution_capability_to_candidate_evidence():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="test_execution",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="Running tests requires test execution.",
            ),
        ],
    )

    support = AgentStarterEvidence(
        key="candidate_supports_test_execution",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Candidate provides test execution.",
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
        evidence=[support],
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
    )

    assert len(assessments) == 1
    assert assessments[0].key == "test_execution"
    assert (
        assessments[0].status
        is TechnicalRequirementStatus.SATISFIED
    )
    assert assessments[0].supporting_evidence == [support]


def test_ocr_requirement_remains_unknown_without_candidate_ocr_evidence():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="ocr_required",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "Scanned document pages require OCR capability."
                ),
            ),
        ],
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="full-rag-pipeline",
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="candidate_uses_retrieval_pipeline",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate uses retrieval.",
            ),
        ],
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
    )

    assert len(assessments) == 1
    assert assessments[0].key == "ocr_required"
    assert (
        assessments[0].status
        is TechnicalRequirementStatus.UNKNOWN
    )
