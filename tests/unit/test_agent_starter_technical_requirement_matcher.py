from schemas.agent_starter import (
    AgentStarterEvidence,
    EvidenceSource,
    TechnicalRequirementStatus,
)


def test_required_capability_is_satisfied_by_explicit_candidate_support():
    from observer.core.agent_starter_technical_requirement_matcher import (
        assess_agent_starter_technical_requirement,
    )

    required = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Code modification requires filesystem write.",
    )

    candidate_support = AgentStarterEvidence(
        key="candidate_supports_filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="The candidate exposes filesystem write.",
    )

    assessment = assess_agent_starter_technical_requirement(
        required_capability=required,
        candidate_evidence=[candidate_support],
        candidate_evidence_key="candidate_supports_filesystem_write",
    )

    assert assessment.key == "filesystem_write"
    assert assessment.status is TechnicalRequirementStatus.SATISFIED
    assert assessment.supporting_evidence == [candidate_support]


def test_required_capability_is_unsatisfied_by_explicit_candidate_lack():
    from observer.core.agent_starter_technical_requirement_matcher import (
        assess_agent_starter_technical_requirement,
    )

    required = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Code modification requires filesystem write.",
    )

    candidate_support = AgentStarterEvidence(
        key="candidate_supports_filesystem_write",
        source=EvidenceSource.DERIVED,
        value=False,
        reason="The candidate cannot modify files.",
    )

    assessment = assess_agent_starter_technical_requirement(
        required_capability=required,
        candidate_evidence=[candidate_support],
        candidate_evidence_key="candidate_supports_filesystem_write",
    )

    assert assessment.status is TechnicalRequirementStatus.UNSATISFIED
    assert assessment.supporting_evidence == [candidate_support]


def test_missing_candidate_capability_evidence_remains_unknown():
    from observer.core.agent_starter_technical_requirement_matcher import (
        assess_agent_starter_technical_requirement,
    )

    required = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Code modification requires filesystem write.",
    )

    assessment = assess_agent_starter_technical_requirement(
        required_capability=required,
        candidate_evidence=[],
        candidate_evidence_key="candidate_supports_filesystem_write",
    )

    assert assessment.status is TechnicalRequirementStatus.UNKNOWN
    assert assessment.supporting_evidence == []


def test_unknown_candidate_capability_evidence_remains_unknown():
    from observer.core.agent_starter_technical_requirement_matcher import (
        assess_agent_starter_technical_requirement,
    )

    required = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Code modification requires filesystem write.",
    )

    unknown = AgentStarterEvidence(
        key="candidate_supports_filesystem_write",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason="Filesystem write support has not been established.",
    )

    assessment = assess_agent_starter_technical_requirement(
        required_capability=required,
        candidate_evidence=[unknown],
        candidate_evidence_key="candidate_supports_filesystem_write",
    )

    assert assessment.status is TechnicalRequirementStatus.UNKNOWN
    assert assessment.supporting_evidence == [unknown]


def test_matcher_does_not_infer_capability_from_architecture_identity():
    from observer.core.agent_starter_technical_requirement_matcher import (
        assess_agent_starter_technical_requirement,
    )

    required = AgentStarterEvidence(
        key="filesystem_write",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Code modification requires filesystem write.",
    )

    unrelated = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=False,
        reason="The architecture processes source code locally.",
    )

    assessment = assess_agent_starter_technical_requirement(
        required_capability=required,
        candidate_evidence=[unrelated],
        candidate_evidence_key="candidate_supports_filesystem_write",
    )

    assert assessment.status is TechnicalRequirementStatus.UNKNOWN
