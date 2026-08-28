from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterPreparedInput,
    AgentStarterRequirement,
    ConstraintStrength,
    EvidenceSource,
    TechnicalRequirementStatus,
)


def _filesystem_write_requirement() -> AgentStarterRequirement:
    evidence = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Code modification requires filesystem write.",
    )

    return AgentStarterRequirement(
        key="filesystem_write",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )


def test_builds_satisfied_filesystem_write_assessment():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        requirements=[_filesystem_write_requirement()],
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
            prepared=prepared,
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

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        requirements=[_filesystem_write_requirement()],
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
            prepared=prepared,
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

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        requirements=[_filesystem_write_requirement()],
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="unknown-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
    )

    assert len(assessments) == 1
    assert (
        assessments[0].status
        is TechnicalRequirementStatus.UNKNOWN
    )


def test_unmapped_requirement_is_not_silently_inferred():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    evidence = AgentStarterEvidence(
        key="shell_execution",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Running tests requires shell execution.",
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        requirements=[
            AgentStarterRequirement(
                key="shell_execution",
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=[evidence],
            ),
        ],
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="source_code_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="Source code remains local.",
            ),
        ],
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
    )

    assert assessments == []


def test_soft_requirement_is_not_a_hard_technical_blocker():
    from observer.core.agent_starter_technical_requirement_orchestrator import (
        build_agent_starter_technical_requirement_assessments,
    )

    evidence = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Filesystem write is preferred.",
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        requirements=[
            AgentStarterRequirement(
                key="filesystem_write",
                value=True,
                strength=ConstraintStrength.SOFT,
                evidence=[evidence],
            ),
        ],
    )

    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assessments = (
        build_agent_starter_technical_requirement_assessments(
            prepared=prepared,
            candidate=candidate,
        )
    )

    assert assessments == []
