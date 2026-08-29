from observer.core.agent_starter_questionnaire import (
    build_agent_starter_question_set,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    EvidenceSource,
)
from schemas.agent_starter_questionnaire import (
    AgentStarterQuestionKind,
)


def test_automation_questionnaire_asks_only_decision_relevant_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
    )

    question_set = build_agent_starter_question_set(intake)

    assert question_set.goal is AgentStarterGoal.AUTOMATION

    assert [
        question.key
        for question in question_set.questions
    ] == [
        "workflow_deterministic",
        "destructive_or_high_impact_actions",
        "human_approval_required",
        "availability_24_7_required",
    ]

    assert all(
        question.kind is AgentStarterQuestionKind.BOOLEAN
        for question in question_set.questions
    )


def test_questionnaire_omits_declared_and_explicitly_unknown_answers():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="workflow_deterministic",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="availability_24_7_required",
                source=EvidenceSource.UNKNOWN,
                reason=(
                    "The user does not yet know whether continuous "
                    "availability is required."
                ),
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert [
        question.key
        for question in question_set.questions
    ] == [
        "destructive_or_high_impact_actions",
        "human_approval_required",
    ]


def test_observed_evidence_does_not_replace_user_intent_answer():
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

    question_set = build_agent_starter_question_set(intake)

    assert "workflow_deterministic" in {
        question.key
        for question in question_set.questions
    }


def test_automation_omits_approval_when_high_impact_actions_are_false():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="destructive_or_high_impact_actions",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert [
        question.key
        for question in question_set.questions
    ] == [
        "workflow_deterministic",
        "availability_24_7_required",
    ]


def test_observed_low_impact_does_not_suppress_user_questions():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.AUTOMATION,
        evidence=[
            AgentStarterEvidence(
                key="destructive_or_high_impact_actions",
                source=EvidenceSource.OBSERVED,
                value=False,
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert [
        question.key
        for question in question_set.questions
    ] == [
        "workflow_deterministic",
        "destructive_or_high_impact_actions",
        "human_approval_required",
        "availability_24_7_required",
    ]


def test_coding_questionnaire_asks_decision_relevant_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
    )

    question_set = build_agent_starter_question_set(intake)

    assert question_set.goal is AgentStarterGoal.CODING
    assert [
        question.key
        for question in question_set.questions
    ] == [
        "source_code_must_stay_local",
        "modify_files",
        "run_tests",
    ]


def test_coding_questionnaire_omits_answered_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="source_code_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.UNKNOWN,
                reason=(
                    "The user has not decided whether the agent "
                    "may modify repository files."
                ),
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert [
        question.key
        for question in question_set.questions
    ] == [
        "run_tests",
    ]


def test_observed_coding_activity_does_not_replace_declared_intent():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.CODING,
        evidence=[
            AgentStarterEvidence(
                key="modify_files",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert "modify_files" in {
        question.key
        for question in question_set.questions
    }


def test_knowledge_questionnaire_asks_decision_relevant_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
    )

    question_set = build_agent_starter_question_set(intake)

    assert question_set.goal is AgentStarterGoal.KNOWLEDGE_RAG
    assert [
        question.key
        for question in question_set.questions
    ] == [
        "knowledge_data_must_stay_local",
        "corpus_is_very_small",
        "document_input_includes_scanned_pages",
        "user_requires_citations",
        "knowledge_changes_frequently",
        "exact_identifier_search_needed",
    ]


def test_knowledge_questionnaire_omits_answered_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="knowledge_data_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="corpus_is_very_small",
                source=EvidenceSource.UNKNOWN,
                reason=(
                    "The user cannot yet estimate whether the "
                    "corpus is very small."
                ),
            ),
            AgentStarterEvidence(
                key="user_requires_citations",
                source=EvidenceSource.DECLARED,
                value=False,
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert [
        question.key
        for question in question_set.questions
    ] == [
        "document_input_includes_scanned_pages",
        "knowledge_changes_frequently",
        "exact_identifier_search_needed",
    ]


def test_observed_knowledge_characteristics_do_not_replace_user_answers():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        evidence=[
            AgentStarterEvidence(
                key="corpus_is_very_small",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert "corpus_is_very_small" in {
        question.key
        for question in question_set.questions
    }


def test_voice_questionnaire_asks_decision_relevant_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
    )

    question_set = build_agent_starter_question_set(intake)

    assert question_set.goal is AgentStarterGoal.VOICE
    assert [
        question.key
        for question in question_set.questions
    ] == [
        "raw_audio_must_stay_local",
        "transcript_must_stay_local",
        "voice_realtime_interaction_requested",
        "voice_interruptions_requested",
    ]


def test_voice_questionnaire_omits_answered_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="raw_audio_must_stay_local",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="voice_realtime_interaction_requested",
                source=EvidenceSource.UNKNOWN,
                reason=(
                    "The user has not decided whether realtime "
                    "interaction is required."
                ),
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert [
        question.key
        for question in question_set.questions
    ] == [
        "transcript_must_stay_local",
        "voice_interruptions_requested",
    ]


def test_observed_voice_behavior_does_not_replace_user_intent():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.VOICE,
        evidence=[
            AgentStarterEvidence(
                key="voice_interruptions_requested",
                source=EvidenceSource.OBSERVED,
                value=False,
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert "voice_interruptions_requested" in {
        question.key
        for question in question_set.questions
    }


def test_personal_questionnaire_asks_decision_relevant_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
    )

    question_set = build_agent_starter_question_set(intake)

    assert question_set.goal is AgentStarterGoal.PERSONAL
    assert [
        question.key
        for question in question_set.questions
    ] == [
        "cross_session_memory_required",
        "proactive_behavior_required",
        "selective_memory_required",
        "indefinite_all_conversation_retention_required",
    ]


def test_personal_questionnaire_omits_answered_inputs():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="cross_session_memory_required",
                source=EvidenceSource.DECLARED,
                value=True,
            ),
            AgentStarterEvidence(
                key="selective_memory_required",
                source=EvidenceSource.UNKNOWN,
                reason=(
                    "The user has not decided whether selective "
                    "memory controls are required."
                ),
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert [
        question.key
        for question in question_set.questions
    ] == [
        "proactive_behavior_required",
        "indefinite_all_conversation_retention_required",
    ]


def test_observed_personal_behavior_does_not_replace_user_intent():
    intake = AgentStarterIntake(
        goal=AgentStarterGoal.PERSONAL,
        evidence=[
            AgentStarterEvidence(
                key="cross_session_memory_required",
                source=EvidenceSource.OBSERVED,
                value=True,
            ),
        ],
    )

    question_set = build_agent_starter_question_set(intake)

    assert "cross_session_memory_required" in {
        question.key
        for question in question_set.questions
    }
