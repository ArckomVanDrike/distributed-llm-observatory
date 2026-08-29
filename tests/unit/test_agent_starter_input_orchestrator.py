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
        "ocr_required",
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
        "ocr_required",
    ]

    assert [
        evidence.value
        for evidence in derived
    ] == [
        True,
        False,
        True,
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
        "source_provenance_required",
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
        "source_provenance_required",
        "corpus_updates_frequent",
        "exact_identifier_lookup_required",
    ]


def test_realtime_voice_request_derives_realtime_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_realtime_interaction_requested",
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
        "realtime_voice_required",
    ]
    assert derived[0].source is EvidenceSource.DERIVED
    assert derived[0].value is True
    assert derived[0].reason


def test_voice_interruptions_request_derives_interruptions_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_interruptions_requested",
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
        "interruptions_required",
        "barge_in_turn_management_required",
    ]
    assert derived[0].source is EvidenceSource.DERIVED
    assert derived[0].value is True
    assert derived[0].reason


def test_uploaded_audio_does_not_imply_realtime_voice():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_input_is_uploaded_audio",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_voice_requirement_rules_do_not_leak_into_other_goals():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="voice_realtime_interaction_requested",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="voice_interruptions_requested",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_voice_requirements_accumulate_in_canonical_order():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_interruptions_requested",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="voice_realtime_interaction_requested",
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
        "realtime_voice_required",
        "interruptions_required",
        "barge_in_turn_management_required",
    ]


def test_false_voice_requests_do_not_derive_requirements():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_realtime_interaction_requested",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
            AgentStarterEvidence(
                key="voice_interruptions_requested",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_observed_voice_behavior_does_not_derive_user_requirements():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_realtime_interaction_requested",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
            AgentStarterEvidence(
                key="voice_interruptions_requested",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_deterministic_automation_derives_no_semantic_interpretation():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
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

    derived = derive_agent_starter_capability_evidence(intake)

    assert [
        evidence.key
        for evidence in derived
    ] == [
        "semantic_interpretation_required",
    ]

    evidence = derived[0]

    assert evidence.source is EvidenceSource.DERIVED
    assert evidence.value is False
    assert evidence.reason


def test_non_deterministic_workflow_does_not_assume_semantic_interpretation():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_observed_deterministic_workflow_does_not_derive_user_intent():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_automation_deterministic_rule_does_not_leak_into_other_goals():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_capability_evidence(intake) == []


def test_build_user_evidence_preserves_intake_and_appends_derived_evidence():
    from observer.core.agent_starter_input_orchestrator import (
        build_agent_starter_user_evidence,
    )

    workflow = AgentStarterEvidence(
        key="workflow_deterministic",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    availability = AgentStarterEvidence(
        key="availability_24_7_required",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            workflow,
            availability,
        ],
    )

    evidence = build_agent_starter_user_evidence(intake)

    assert [
        item.key
        for item in evidence
    ] == [
        "workflow_deterministic",
        "availability_24_7_required",
        "semantic_interpretation_required",
    ]

    assert evidence[0] == workflow
    assert evidence[1] == availability

    assert evidence[2].source is EvidenceSource.DERIVED
    assert evidence[2].value is False
    assert evidence[2].reason


def test_build_user_evidence_preserves_observed_and_unknown_provenance():
    from observer.core.agent_starter_input_orchestrator import (
        build_agent_starter_user_evidence,
    )

    observed = AgentStarterEvidence(
        key="microphone_available",
        source=EvidenceSource.OBSERVED,
        value=True,
    )
    unknown = AgentStarterEvidence(
        key="accelerator_details_available",
        source=EvidenceSource.UNKNOWN,
        value=None,
        reason="The browser does not expose accelerator details.",
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            observed,
            unknown,
        ],
    )

    evidence = build_agent_starter_user_evidence(intake)

    assert evidence == [
        observed,
        unknown,
    ]
    assert evidence[0].source is EvidenceSource.OBSERVED
    assert evidence[1].source is EvidenceSource.UNKNOWN


def test_build_user_evidence_does_not_mutate_intake():
    from observer.core.agent_starter_input_orchestrator import (
        build_agent_starter_user_evidence,
    )

    declared = AgentStarterEvidence(
        key="modify_files",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[declared],
    )

    original = list(intake.evidence)

    evidence = build_agent_starter_user_evidence(intake)

    assert intake.evidence == original

    assert [
        item.key
        for item in evidence
    ] == [
        "modify_files",
        "filesystem_read",
        "filesystem_write",
    ]


def test_prepare_agent_starter_input_composes_normalized_inputs():
    from observer.core.agent_starter_input_orchestrator import (
        prepare_agent_starter_input,
    )
    from schemas.hardware import (
        DeviceClass,
        HardwareProfile,
        HardwareProfileSource,
    )

    local_only = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    modify_files = AgentStarterEvidence(
        key="modify_files",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=16 * 1024**3,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            local_only,
            modify_files,
        ],
        hardware_profile=hardware,
    )

    prepared = prepare_agent_starter_input(intake)

    assert prepared.goal is AgentStarterGoal.CODING
    assert prepared.hardware_profile == hardware

    assert [
        evidence.key
        for evidence in prepared.evidence
    ] == [
        "source_code_must_stay_local",
        "modify_files",
        "filesystem_read",
        "filesystem_write",
    ]

    assert [
        requirement.key
        for requirement in prepared.requirements
    ] == [
        "source_code_must_stay_local",
    ]

    assert prepared.requirements[0].strength is ConstraintStrength.HARD
    assert prepared.requirements[0].evidence == [local_only]


def test_prepare_agent_starter_input_preserves_incomplete_state():
    from observer.core.agent_starter_input_orchestrator import (
        prepare_agent_starter_input,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
    )

    prepared = prepare_agent_starter_input(intake)

    assert prepared.goal is AgentStarterGoal.PERSONAL
    assert prepared.evidence == []
    assert prepared.requirements == []
    assert prepared.hardware_profile is None


def test_prepare_agent_starter_input_does_not_mutate_intake():
    from observer.core.agent_starter_input_orchestrator import (
        prepare_agent_starter_input,
    )

    declared = AgentStarterEvidence(
        key="workflow_deterministic",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[declared],
    )

    original_evidence = list(intake.evidence)

    prepared = prepare_agent_starter_input(intake)

    assert intake.evidence == original_evidence

    assert [
        evidence.key
        for evidence in prepared.evidence
    ] == [
        "workflow_deterministic",
        "semantic_interpretation_required",
    ]


def test_scanned_rag_documents_derive_ocr_requirement():
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

    ocr_required = [
        evidence
        for evidence in derived
        if evidence.key == "ocr_required"
    ]

    assert len(ocr_required) == 1
    assert ocr_required[0].source is EvidenceSource.DERIVED
    assert ocr_required[0].value is True
    assert ocr_required[0].reason


def test_rag_citations_derive_source_provenance_requirement():
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

    provenance_required = [
        evidence
        for evidence in derived
        if evidence.key == "source_provenance_required"
    ]

    assert len(provenance_required) == 1
    assert (
        provenance_required[0].source
        is EvidenceSource.DERIVED
    )
    assert provenance_required[0].value is True
    assert provenance_required[0].reason


def test_voice_interruptions_derive_turn_management_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_interruptions_requested",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    turn_management_required = [
        evidence
        for evidence in derived
        if (
            evidence.key
            == "barge_in_turn_management_required"
        )
    ]

    assert len(turn_management_required) == 1
    assert (
        turn_management_required[0].source
        is EvidenceSource.DERIVED
    )
    assert turn_management_required[0].value is True
    assert turn_management_required[0].reason


def test_cross_session_memory_derives_persistent_memory_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="cross_session_memory_required",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    persistent_memory_required = [
        evidence
        for evidence in derived
        if evidence.key == "persistent_memory_required"
    ]

    assert len(persistent_memory_required) == 1
    assert (
        persistent_memory_required[0].source
        is EvidenceSource.DERIVED
    )
    assert persistent_memory_required[0].value is True
    assert persistent_memory_required[0].reason


def test_proactive_personal_behavior_derives_background_scheduling_requirement():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_capability_evidence,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="proactive_behavior_required",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    derived = derive_agent_starter_capability_evidence(intake)

    scheduling_required = [
        evidence
        for evidence in derived
        if evidence.key == "background_scheduling_required"
    ]

    assert len(scheduling_required) == 1
    assert (
        scheduling_required[0].source
        is EvidenceSource.DERIVED
    )
    assert scheduling_required[0].value is True
    assert scheduling_required[0].reason


def test_derives_cross_cutting_offline_and_soft_preference_requirements():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterGoal,
        AgentStarterIntake,
        ConstraintStrength,
        EvidenceSource,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="offline_required",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="prefer_local_execution",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="prefer_low_complexity",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    requirements = derive_agent_starter_requirements(intake)

    assert [
        (requirement.key, requirement.strength)
        for requirement in requirements
    ] == [
        (
            "offline_required",
            ConstraintStrength.HARD,
        ),
        (
            "prefer_local_execution",
            ConstraintStrength.SOFT,
        ),
        (
            "prefer_low_complexity",
            ConstraintStrength.SOFT,
        ),
    ]

    assert all(
        requirement.evidence[0]
        in intake.evidence
        for requirement in requirements
    )


def test_requirement_derivation_does_not_promote_observed_or_false_preferences():
    from observer.core.agent_starter_input_orchestrator import (
        derive_agent_starter_requirements,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterGoal,
        AgentStarterIntake,
        EvidenceSource,
    )

    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="offline_required",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
            AgentStarterEvidence(
                key="prefer_local_execution",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
            AgentStarterEvidence(
                key="prefer_low_complexity",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    assert derive_agent_starter_requirements(intake) == []
