from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    ConstraintStrength,
    EvidenceSource,
)


def test_derives_hard_local_code_requirement_from_declared_intake():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    declared = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[declared],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert len(requirements) == 1

    requirement = requirements[0]

    assert requirement.key == "source_code_must_stay_local"
    assert requirement.value is True
    assert requirement.strength is ConstraintStrength.HARD
    assert requirement.evidence == [declared]


def test_does_not_invent_local_code_requirement_when_absent():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
    )

    requirements = derive_agent_starter_requirements(intake)

    assert requirements == []


def test_declared_remote_allowed_does_not_become_local_only_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="source_code_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert requirements == []


def test_observed_local_processing_does_not_become_hard_user_constraint():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="source_code_must_stay_local",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert requirements == []


def test_derives_hard_knowledge_local_requirement_from_declared_intake():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    declared = AgentStarterEvidence(
        key="knowledge_data_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[declared],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert len(requirements) == 1

    requirement = requirements[0]

    assert requirement.key == "knowledge_data_must_stay_local"
    assert requirement.value is True
    assert requirement.strength is ConstraintStrength.HARD
    assert requirement.evidence == [declared]


def test_declared_remote_knowledge_allowed_does_not_become_local_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="knowledge_data_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert requirements == []


def test_observed_local_knowledge_processing_is_not_hard_user_constraint():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="knowledge_data_must_stay_local",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert requirements == []


def test_derives_hard_raw_audio_local_requirement_from_declared_intake():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    declared = AgentStarterEvidence(
        key="raw_audio_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[declared],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert len(requirements) == 1
    requirement = requirements[0]

    assert requirement.key == "raw_audio_must_stay_local"
    assert requirement.value is True
    assert requirement.strength is ConstraintStrength.HARD
    assert requirement.evidence == [declared]


def test_derives_hard_transcript_local_requirement_from_declared_intake():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    declared = AgentStarterEvidence(
        key="transcript_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[declared],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert len(requirements) == 1
    requirement = requirements[0]

    assert requirement.key == "transcript_must_stay_local"
    assert requirement.value is True
    assert requirement.strength is ConstraintStrength.HARD
    assert requirement.evidence == [declared]


def test_voice_privacy_boundaries_are_independent():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="raw_audio_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="transcript_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert [
        requirement.key
        for requirement in requirements
    ] == [
        "raw_audio_must_stay_local",
    ]


def test_observed_voice_locality_does_not_become_hard_user_constraint():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="raw_audio_must_stay_local",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
            AgentStarterEvidence(
                key="transcript_must_stay_local",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert requirements == []


def test_voice_multiple_local_privacy_requirements_are_preserved_in_order():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="transcript_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="raw_audio_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert [
        requirement.key
        for requirement in requirements
    ] == [
        "raw_audio_must_stay_local",
        "transcript_must_stay_local",
    ]

    assert all(
        requirement.strength is ConstraintStrength.HARD
        for requirement in requirements
    )


def test_derives_coding_capabilities_from_modify_files_and_run_tests():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
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

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "filesystem_read",
        "filesystem_write",
        "shell_execution",
        "test_execution",
    ]

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for evidence in derived
    )
    assert all(
        evidence.value is True
        for evidence in derived
    )
    assert all(
        evidence.reason
        for evidence in derived
    )


def test_does_not_invent_coding_capabilities_without_user_intent():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_false_coding_intent_does_not_derive_capabilities():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
            AgentStarterEvidence(
                key="run_tests",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_modify_files_alone_derives_filesystem_capabilities():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
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

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "filesystem_read",
        "filesystem_write",
    ]

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for evidence in derived
    )
    assert all(
        evidence.reason
        for evidence in derived
    )


def test_run_tests_alone_derives_shell_and_test_capabilities():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
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

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "shell_execution",
        "test_execution",
    ]

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for evidence in derived
    )
    assert all(
        evidence.reason
        for evidence in derived
    )


def test_observed_coding_activity_does_not_derive_user_intent_capabilities():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
            AgentStarterEvidence(
                key="run_tests",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    assert derived == []


def test_coding_capability_rules_do_not_leak_into_other_goals():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
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

    assert derive_agent_starter_capability_evidence(intake) == []


def test_very_small_rag_corpus_derives_direct_context_without_retrieval():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="corpus_is_very_small",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "corpus_fits_direct_context",
        "retrieval_required",
    ]

    assert derived[0].value is True
    assert derived[1].value is False

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for evidence in derived
    )
    assert all(
        evidence.reason
        for evidence in derived
    )


def test_small_corpus_rag_rule_does_not_leak_into_other_goals():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="corpus_is_very_small",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_false_small_corpus_claim_does_not_assume_retrieval_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="corpus_is_very_small",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_scanned_document_input_derives_rag_scan_requirement_evidence():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="document_input_includes_scanned_pages",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "documents_include_scans",
    ]

    evidence = derived[0]

    assert evidence.source is EvidenceSource.DERIVED
    assert evidence.value is True
    assert evidence.reason


def test_false_scanned_document_input_does_not_derive_scan_evidence():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="document_input_includes_scanned_pages",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_rag_scan_rule_does_not_leak_into_other_goals():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="document_input_includes_scanned_pages",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_rag_capability_derivations_accumulate_independent_signals():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="document_input_includes_scanned_pages",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="corpus_is_very_small",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "corpus_fits_direct_context",
        "retrieval_required",
        "documents_include_scans",
    ]

    assert [
        evidence.value
        for evidence in derived
    ] == [
        True,
        False,
        True,
    ]

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for evidence in derived
    )


def test_rag_citation_request_derives_citations_required():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="user_requires_citations",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "citations_required",
    ]
    assert derived[0].source is EvidenceSource.DERIVED
    assert derived[0].value is True
    assert derived[0].reason


def test_frequently_changing_knowledge_derives_update_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="knowledge_changes_frequently",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "corpus_updates_frequent",
    ]
    assert derived[0].source is EvidenceSource.DERIVED
    assert derived[0].value is True
    assert derived[0].reason


def test_exact_identifier_search_derives_lookup_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="exact_identifier_search_needed",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "exact_identifier_lookup_required",
    ]
    assert derived[0].source is EvidenceSource.DERIVED
    assert derived[0].value is True
    assert derived[0].reason


def test_false_rag_preferences_do_not_derive_requirements():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="user_requires_citations",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
            AgentStarterEvidence(
                key="knowledge_changes_frequently",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
            AgentStarterEvidence(
                key="exact_identifier_search_needed",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_observed_rag_preferences_do_not_derive_user_intent():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="user_requires_citations",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
            AgentStarterEvidence(
                key="knowledge_changes_frequently",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
            AgentStarterEvidence(
                key="exact_identifier_search_needed",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_rag_decision_evidence_has_canonical_order():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="exact_identifier_search_needed",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="user_requires_citations",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="knowledge_changes_frequently",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "citations_required",
        "corpus_updates_frequent",
        "exact_identifier_lookup_required",
    ]
