from observer.core.agent_starter_candidate_generator import (
    generate_agent_starter_candidates,
)
from schemas.agent_starter import (
    AgentStarterGoal,
    AgentStarterPreparedInput,
    EvidenceSource,
)


def test_generates_base_coding_candidates_in_deterministic_order():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "local-coding-agent",
        "remote-coding-agent",
    ]

    assert all(
        candidate.goal is AgentStarterGoal.CODING
        for candidate in candidates
    )


def test_coding_candidates_record_locality_evidence():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    candidates = generate_agent_starter_candidates(
        prepared,
    )

    local_candidate, remote_candidate = candidates

    assert any(
        evidence.key == "source_code_remote_processing"
        and evidence.source is EvidenceSource.DERIVED
        and evidence.value is False
        for evidence in local_candidate.evidence
    )

    assert any(
        evidence.key == "source_code_remote_processing"
        and evidence.source is EvidenceSource.DERIVED
        and evidence.value is True
        for evidence in remote_candidate.evidence
    )


def test_coding_candidate_generation_does_not_filter_hard_privacy_conflicts():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterRequirement,
        ConstraintStrength,
    )

    declared = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        evidence=[declared],
        requirements=[
            AgentStarterRequirement(
                key="source_code_must_stay_local",
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=[declared],
            ),
        ],
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "local-coding-agent",
        "remote-coding-agent",
    ]


def test_coding_candidate_generation_does_not_add_assessment_state():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    candidates = generate_agent_starter_candidates(prepared)

    for candidate in candidates:
        assert not hasattr(candidate, "technical_feasibility")
        assert not hasattr(candidate, "recommendation")
        assert not hasattr(candidate, "confidence")


def test_candidate_generation_supports_all_agent_starter_goals():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    for goal in AgentStarterGoal:
        prepared = AgentStarterPreparedInput(
            goal=goal,
        )

        assert generate_agent_starter_candidates(prepared)


def test_generates_base_rag_candidates_in_deterministic_order():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "direct-context-knowledge-assistant",
        "full-rag-pipeline",
    ]

    assert all(
        candidate.goal is AgentStarterGoal.KNOWLEDGE_RAG
        for candidate in candidates
    )


def test_rag_candidates_record_retrieval_architecture_evidence():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
    )

    candidates = generate_agent_starter_candidates(
        prepared,
    )

    direct_context, full_rag = candidates

    assert any(
        evidence.key == "candidate_uses_retrieval_pipeline"
        and evidence.source is EvidenceSource.DERIVED
        and evidence.value is False
        for evidence in direct_context.evidence
    )

    assert any(
        evidence.key == "candidate_uses_retrieval_pipeline"
        and evidence.source is EvidenceSource.DERIVED
        and evidence.value is True
        for evidence in full_rag.evidence
    )


def test_rag_candidate_generation_does_not_filter_unneeded_retrieval():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from schemas.agent_starter import AgentStarterEvidence

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="retrieval_required",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The declared corpus is small enough "
                    "for direct context."
                ),
            ),
        ],
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "direct-context-knowledge-assistant",
        "full-rag-pipeline",
    ]


def test_generates_base_voice_candidates_in_deterministic_order():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.VOICE,
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "local-voice-pipeline",
        "hybrid-voice-pipeline",
        "cloud-voice-pipeline",
    ]

    assert all(
        candidate.goal is AgentStarterGoal.VOICE
        for candidate in candidates
    )


def test_voice_candidates_record_audio_and_transcript_locality():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.VOICE,
    )

    candidates = generate_agent_starter_candidates(
        prepared,
    )

    local_voice, hybrid_voice, cloud_voice = candidates

    def locality(candidate):
        return {
            evidence.key: evidence.value
            for evidence in candidate.evidence
            if evidence.key in {
                "candidate_raw_audio_remote_processing",
                "candidate_transcript_remote_processing",
            }
        }

    assert locality(local_voice) == {
        "candidate_raw_audio_remote_processing": False,
        "candidate_transcript_remote_processing": False,
    }

    assert locality(hybrid_voice) == {
        "candidate_raw_audio_remote_processing": False,
        "candidate_transcript_remote_processing": True,
    }

    assert locality(cloud_voice) == {
        "candidate_raw_audio_remote_processing": True,
        "candidate_transcript_remote_processing": True,
    }


def test_voice_candidate_generation_does_not_filter_privacy_conflicts():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterRequirement,
        ConstraintStrength,
    )

    raw_audio_local = AgentStarterEvidence(
        key="raw_audio_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    transcript_local = AgentStarterEvidence(
        key="transcript_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            raw_audio_local,
            transcript_local,
        ],
        requirements=[
            AgentStarterRequirement(
                key="raw_audio_must_stay_local",
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=[raw_audio_local],
            ),
            AgentStarterRequirement(
                key="transcript_must_stay_local",
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=[transcript_local],
            ),
        ],
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "local-voice-pipeline",
        "hybrid-voice-pipeline",
        "cloud-voice-pipeline",
    ]


def test_generates_base_automation_candidates_in_deterministic_order():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.AUTOMATION,
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "traditional-deterministic-automation",
        "supervised-automation-agent",
        "autonomous-workflow-agent",
    ]

    assert all(
        candidate.goal is AgentStarterGoal.AUTOMATION
        for candidate in candidates
    )


def test_automation_candidates_record_llm_and_autonomy_properties():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.AUTOMATION,
    )

    traditional, supervised, autonomous = (
        generate_agent_starter_candidates(prepared)
    )

    assert {
        evidence.key: evidence.value
        for evidence in traditional.evidence
    } == {
        "candidate_uses_llm": False,
    }

    assert {
        evidence.key: evidence.value
        for evidence in supervised.evidence
    } == {
        "candidate_uses_llm": True,
        "candidate_executes_autonomously": False,
    }

    assert {
        evidence.key: evidence.value
        for evidence in autonomous.evidence
    } == {
        "candidate_uses_llm": True,
        "candidate_executes_autonomously": True,
    }

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for candidate in (traditional, supervised, autonomous)
        for evidence in candidate.evidence
    )

    assert all(
        evidence.reason
        for candidate in (traditional, supervised, autonomous)
        for evidence in candidate.evidence
    )


def test_automation_generation_does_not_filter_deterministic_workflows():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from schemas.agent_starter import AgentStarterEvidence

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="semantic_interpretation_required",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The declared workflow is deterministic and "
                    "does not require semantic interpretation."
                ),
            ),
        ],
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "traditional-deterministic-automation",
        "supervised-automation-agent",
        "autonomous-workflow-agent",
    ]


def test_generates_base_personal_candidates_in_deterministic_order():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.PERSONAL,
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "session-only-personal-assistant",
        "opaque-persistent-memory-assistant",
        "controlled-persistent-memory-assistant",
    ]

    assert all(
        candidate.goal is AgentStarterGoal.PERSONAL
        for candidate in candidates
    )


def test_personal_candidates_record_memory_properties():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.PERSONAL,
    )

    session_only, opaque_memory, controlled_memory = (
        generate_agent_starter_candidates(prepared)
    )

    assert {
        evidence.key: evidence.value
        for evidence in session_only.evidence
            if evidence.key != "candidate_uses_llm"
    } == {
        "candidate_supports_persistent_memory": False,
    }

    assert {
        evidence.key: evidence.value
        for evidence in opaque_memory.evidence
            if evidence.key != "candidate_uses_llm"
    } == {
        "candidate_supports_persistent_memory": True,
        "candidate_supports_memory_inspect_edit_delete": False,
    }

    assert {
        evidence.key: evidence.value
        for evidence in controlled_memory.evidence
            if evidence.key != "candidate_uses_llm"
    } == {
        "candidate_supports_persistent_memory": True,
        "candidate_supports_memory_inspect_edit_delete": True,
    }

    assert all(
        evidence.source is EvidenceSource.DERIVED
        for candidate in (
            session_only,
            opaque_memory,
            controlled_memory,
        )
        for evidence in candidate.evidence
    )

    assert all(
        evidence.reason
        for candidate in (
            session_only,
            opaque_memory,
            controlled_memory,
        )
        for evidence in candidate.evidence
    )


def test_personal_generation_does_not_filter_selective_memory_conflicts():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from schemas.agent_starter import AgentStarterEvidence

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="selective_memory_required",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
        ],
    )

    candidates = generate_agent_starter_candidates(prepared)

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "session-only-personal-assistant",
        "opaque-persistent-memory-assistant",
        "controlled-persistent-memory-assistant",
    ]


def test_coding_candidates_explicitly_record_filesystem_write_support():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    candidates = generate_agent_starter_candidates(prepared)

    local_candidate, remote_candidate = candidates

    for candidate in (
        local_candidate,
        remote_candidate,
    ):
        matches = [
            evidence
            for evidence in candidate.evidence
            if evidence.key
            == "candidate_supports_filesystem_write"
        ]

        assert len(matches) == 1
        assert matches[0].value is True
        assert matches[0].source is EvidenceSource.DERIVED
        assert matches[0].reason


def test_coding_candidates_explicitly_record_filesystem_read_support():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    local_candidate, remote_candidate = (
        generate_agent_starter_candidates(prepared)
    )

    for candidate in (
        local_candidate,
        remote_candidate,
    ):
        matches = [
            evidence
            for evidence in candidate.evidence
            if evidence.key
            == "candidate_supports_filesystem_read"
        ]

        assert len(matches) == 1
        assert matches[0].value is True
        assert matches[0].source is EvidenceSource.DERIVED
        assert matches[0].reason


def test_coding_candidates_explicitly_record_shell_execution_support():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    local_candidate, remote_candidate = (
        generate_agent_starter_candidates(prepared)
    )

    for candidate in (
        local_candidate,
        remote_candidate,
    ):
        matches = [
            evidence
            for evidence in candidate.evidence
            if evidence.key
            == "candidate_supports_shell_execution"
        ]

        assert len(matches) == 1
        assert matches[0].value is True
        assert matches[0].source is EvidenceSource.DERIVED
        assert matches[0].reason


def test_coding_candidates_explicitly_record_test_execution_support():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    local_candidate, remote_candidate = (
        generate_agent_starter_candidates(prepared)
    )

    for candidate in (
        local_candidate,
        remote_candidate,
    ):
        matches = [
            evidence
            for evidence in candidate.evidence
            if evidence.key
            == "candidate_supports_test_execution"
        ]

        assert len(matches) == 1
        assert matches[0].value is True
        assert matches[0].source is EvidenceSource.DERIVED
        assert matches[0].reason


def test_coding_candidates_explicitly_record_llm_usage():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    candidates = generate_agent_starter_candidates(
        prepared,
    )

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "local-coding-agent",
        "remote-coding-agent",
    ]

    for candidate in candidates:
        llm_usage = [
            evidence.value
            for evidence in candidate.evidence
            if evidence.key == "candidate_uses_llm"
        ]

        assert llm_usage == [True]


def test_rag_candidates_explicitly_record_llm_usage():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
    )

    candidates = generate_agent_starter_candidates(
        prepared,
    )

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "direct-context-knowledge-assistant",
        "full-rag-pipeline",
    ]

    for candidate in candidates:
        llm_usage = [
            evidence.value
            for evidence in candidate.evidence
            if evidence.key == "candidate_uses_llm"
        ]

        assert llm_usage == [True]


def test_voice_candidates_explicitly_record_speech_component_usage():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.VOICE,
    )

    candidates = generate_agent_starter_candidates(
        prepared,
    )

    assert [
        candidate.architecture_id
        for candidate in candidates
    ] == [
        "local-voice-pipeline",
        "hybrid-voice-pipeline",
        "cloud-voice-pipeline",
    ]

    for candidate in candidates:
        stt_usage = [
            evidence.value
            for evidence in candidate.evidence
            if evidence.key == "candidate_uses_stt"
        ]
        tts_usage = [
            evidence.value
            for evidence in candidate.evidence
            if evidence.key == "candidate_uses_tts"
        ]

        assert stt_usage == [True]
        assert tts_usage == [True]


def test_personal_candidates_explicitly_record_llm_usage():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.PERSONAL,
    )

    candidates = generate_agent_starter_candidates(
        prepared,
    )

    assert len(candidates) == 3
    assert len({
        candidate.architecture_id
        for candidate in candidates
    }) == 3

    for candidate in candidates:
        llm_usage = [
            evidence.value
            for evidence in candidate.evidence
            if evidence.key == "candidate_uses_llm"
        ]

        assert llm_usage == [True]


def test_coding_candidates_explicitly_record_execution_mode():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )

    local_candidate, remote_candidate = (
        generate_agent_starter_candidates(prepared)
    )

    def execution_mode(candidate):
        return [
            evidence.value
            for evidence in candidate.evidence
            if evidence.key == "candidate_execution_mode"
        ]

    assert execution_mode(local_candidate) == ["local"]
    assert execution_mode(remote_candidate) == ["remote"]


def test_voice_candidates_explicitly_record_execution_mode():
    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.VOICE,
    )

    local_voice, hybrid_voice, cloud_voice = (
        generate_agent_starter_candidates(prepared)
    )

    def execution_mode(candidate):
        return [
            evidence.value
            for evidence in candidate.evidence
            if evidence.key == "candidate_execution_mode"
        ]

    assert execution_mode(local_voice) == ["local"]
    assert execution_mode(hybrid_voice) == ["hybrid"]
    assert execution_mode(cloud_voice) == ["remote"]


def test_other_goal_candidates_do_not_invent_execution_mode():
    for goal in (
        AgentStarterGoal.KNOWLEDGE_RAG,
        AgentStarterGoal.AUTOMATION,
        AgentStarterGoal.PERSONAL,
    ):
        candidates = generate_agent_starter_candidates(
            AgentStarterPreparedInput(goal=goal)
        )

        assert all(
            not any(
                evidence.key == "candidate_execution_mode"
                for evidence in candidate.evidence
            )
            for candidate in candidates
        )
