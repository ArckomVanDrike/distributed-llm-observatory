from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    AgentStarterRequirement,
    ConstraintStrength,
    EvidenceSource,
)

_HARD_LOCAL_ONLY_REQUIREMENT_KEYS = (
    "source_code_must_stay_local",
    "knowledge_data_must_stay_local",
    "raw_audio_must_stay_local",
    "transcript_must_stay_local",
)


def _declared_true_evidence(
    intake: AgentStarterIntake,
    *,
    key: str,
) -> list[AgentStarterEvidence]:
    return [
        evidence
        for evidence in intake.evidence
        if (
            evidence.key == key
            and evidence.source is EvidenceSource.DECLARED
            and evidence.value is True
        )
    ]


def derive_agent_starter_requirements(
    intake: AgentStarterIntake,
) -> list[AgentStarterRequirement]:
    requirements: list[AgentStarterRequirement] = []

    for key in _HARD_LOCAL_ONLY_REQUIREMENT_KEYS:
        supporting_evidence = _declared_true_evidence(
            intake,
            key=key,
        )

        if not supporting_evidence:
            continue

        requirements.append(
            AgentStarterRequirement(
                key=key,
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=supporting_evidence,
            )
        )

    return requirements


def derive_agent_starter_capability_evidence(
    intake: AgentStarterIntake,
) -> list[AgentStarterEvidence]:
    if intake.goal is AgentStarterGoal.KNOWLEDGE_RAG:
        derived: list[AgentStarterEvidence] = []

        corpus_is_very_small = bool(
            _declared_true_evidence(
                intake,
                key="corpus_is_very_small",
            )
        )

        if corpus_is_very_small:
            reason = (
                "A user-declared very small corpus can fit direct "
                "context without requiring a retrieval pipeline."
            )

            derived.extend(
                [
                    AgentStarterEvidence(
                        key="corpus_fits_direct_context",
                        source=EvidenceSource.DERIVED,
                        value=True,
                        reason=reason,
                    ),
                    AgentStarterEvidence(
                        key="retrieval_required",
                        source=EvidenceSource.DERIVED,
                        value=False,
                        reason=reason,
                    ),
                ]
            )

        documents_include_scanned_pages = bool(
            _declared_true_evidence(
                intake,
                key="document_input_includes_scanned_pages",
            )
        )

        if documents_include_scanned_pages:
            derived.append(
                AgentStarterEvidence(
                    key="documents_include_scans",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The user declared that document input "
                        "includes scanned pages."
                    ),
                )
            )

        user_requires_citations = bool(
            _declared_true_evidence(
                intake,
                key="user_requires_citations",
            )
        )

        if user_requires_citations:
            derived.append(
                AgentStarterEvidence(
                    key="citations_required",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The user explicitly requires citations "
                        "in knowledge answers."
                    ),
                )
            )

        knowledge_changes_frequently = bool(
            _declared_true_evidence(
                intake,
                key="knowledge_changes_frequently",
            )
        )

        if knowledge_changes_frequently:
            derived.append(
                AgentStarterEvidence(
                    key="corpus_updates_frequent",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The user declared that the knowledge "
                        "corpus changes frequently."
                    ),
                )
            )

        exact_identifier_search_needed = bool(
            _declared_true_evidence(
                intake,
                key="exact_identifier_search_needed",
            )
        )

        if exact_identifier_search_needed:
            derived.append(
                AgentStarterEvidence(
                    key="exact_identifier_lookup_required",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The user requires exact identifier "
                        "lookup in the knowledge corpus."
                    ),
                )
            )

        return derived

    if intake.goal is AgentStarterGoal.VOICE:
        derived: list[AgentStarterEvidence] = []

        realtime_requested = bool(
            _declared_true_evidence(
                intake,
                key="voice_realtime_interaction_requested",
            )
        )

        if realtime_requested:
            derived.append(
                AgentStarterEvidence(
                    key="realtime_voice_required",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The user requested realtime voice "
                        "interaction."
                    ),
                )
            )

        interruptions_requested = bool(
            _declared_true_evidence(
                intake,
                key="voice_interruptions_requested",
            )
        )

        if interruptions_requested:
            derived.append(
                AgentStarterEvidence(
                    key="interruptions_required",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=(
                        "The user requested interruption or "
                        "barge-in behavior during voice interaction."
                    ),
                )
            )

        return derived

    if intake.goal is AgentStarterGoal.AUTOMATION:
        workflow_deterministic = bool(
            _declared_true_evidence(
                intake,
                key="workflow_deterministic",
            )
        )

        if not workflow_deterministic:
            return []

        return [
            AgentStarterEvidence(
                key="semantic_interpretation_required",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The user declared a deterministic workflow, "
                    "so semantic interpretation is not required."
                ),
            )
        ]

    if intake.goal is not AgentStarterGoal.CODING:
        return []

    derived: list[AgentStarterEvidence] = []

    modify_files = bool(
        _declared_true_evidence(
            intake,
            key="modify_files",
        )
    )
    run_tests = bool(
        _declared_true_evidence(
            intake,
            key="run_tests",
        )
    )

    if modify_files:
        reason = (
            "Modifying files requires repository filesystem "
            "read and write access."
        )

        derived.extend(
            [
                AgentStarterEvidence(
                    key="filesystem_read",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=reason,
                ),
                AgentStarterEvidence(
                    key="filesystem_write",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=reason,
                ),
            ]
        )

    if run_tests:
        reason = (
            "Running tests requires shell execution and "
            "test execution capabilities."
        )

        derived.extend(
            [
                AgentStarterEvidence(
                    key="shell_execution",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=reason,
                ),
                AgentStarterEvidence(
                    key="test_execution",
                    source=EvidenceSource.DERIVED,
                    value=True,
                    reason=reason,
                ),
            ]
        )

    return derived
