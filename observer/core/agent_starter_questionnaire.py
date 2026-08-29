from __future__ import annotations

from schemas.agent_starter import (
    AgentStarterGoal,
    AgentStarterIntake,
    EvidenceSource,
)
from schemas.agent_starter_questionnaire import (
    AgentStarterQuestion,
    AgentStarterQuestionKind,
    AgentStarterQuestionSet,
)

_CODING_QUESTIONS = (
    AgentStarterQuestion(
        key="source_code_must_stay_local",
        goal=AgentStarterGoal.CODING,
        prompt=(
            "Must the source code remain inside the "
            "user-controlled environment?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Source-code locality is a hard privacy constraint "
            "that can exclude remote coding architectures."
        ),
    ),
    AgentStarterQuestion(
        key="modify_files",
        goal=AgentStarterGoal.CODING,
        prompt="May the coding agent modify repository files?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "File modification requires filesystem read and "
            "write capabilities."
        ),
    ),
    AgentStarterQuestion(
        key="run_tests",
        goal=AgentStarterGoal.CODING,
        prompt="Should the coding agent be able to run tests?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Running tests requires shell and test execution "
            "capabilities."
        ),
    ),
)


_KNOWLEDGE_QUESTIONS = (
    AgentStarterQuestion(
        key="knowledge_data_must_stay_local",
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        prompt=(
            "Must the knowledge data remain inside the "
            "user-controlled environment?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Knowledge-data locality is a hard privacy constraint "
            "that can exclude remote-processing architectures."
        ),
    ),
    AgentStarterQuestion(
        key="corpus_is_very_small",
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        prompt="Is the knowledge corpus very small?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "A very small corpus can make a full retrieval "
            "pipeline unnecessary."
        ),
    ),
    AgentStarterQuestion(
        key="document_input_includes_scanned_pages",
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        prompt="Does the document corpus include scanned pages?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Scanned pages can require OCR capability."
        ),
    ),
    AgentStarterQuestion(
        key="user_requires_citations",
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        prompt="Must answers include citations?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Citation requirements can require explicit "
            "source provenance support."
        ),
    ),
    AgentStarterQuestion(
        key="knowledge_changes_frequently",
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        prompt="Does the knowledge corpus change frequently?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Frequently changing knowledge can make incremental "
            "indexing operationally important."
        ),
    ),
    AgentStarterQuestion(
        key="exact_identifier_search_needed",
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        prompt=(
            "Must the system reliably find exact identifiers "
            "or exact terms?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Exact identifier lookup can require lexical or "
            "hybrid retrieval support."
        ),
    ),
)


_VOICE_QUESTIONS = (
    AgentStarterQuestion(
        key="raw_audio_must_stay_local",
        goal=AgentStarterGoal.VOICE,
        prompt=(
            "Must raw audio remain inside the "
            "user-controlled environment?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Raw-audio locality is a hard privacy constraint "
            "that can exclude remote voice architectures."
        ),
    ),
    AgentStarterQuestion(
        key="transcript_must_stay_local",
        goal=AgentStarterGoal.VOICE,
        prompt=(
            "Must transcripts remain inside the "
            "user-controlled environment?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Transcript locality can exclude architectures "
            "that process text remotely."
        ),
    ),
    AgentStarterQuestion(
        key="voice_realtime_interaction_requested",
        goal=AgentStarterGoal.VOICE,
        prompt="Is realtime voice interaction required?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Realtime interaction can require streaming and "
            "acceptable end-to-end latency."
        ),
    ),
    AgentStarterQuestion(
        key="voice_interruptions_requested",
        goal=AgentStarterGoal.VOICE,
        prompt=(
            "Must the user be able to interrupt the assistant "
            "while it is speaking?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Interruptions can require barge-in and conversational "
            "turn-management support."
        ),
    ),
)


_PERSONAL_QUESTIONS = (
    AgentStarterQuestion(
        key="cross_session_memory_required",
        goal=AgentStarterGoal.PERSONAL,
        prompt=(
            "Must the assistant remember information "
            "across separate sessions?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Cross-session memory can require persistent "
            "memory capability."
        ),
    ),
    AgentStarterQuestion(
        key="proactive_behavior_required",
        goal=AgentStarterGoal.PERSONAL,
        prompt=(
            "Must the assistant act proactively without "
            "waiting for a new user message?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Proactive behavior can require scheduled or "
            "background execution."
        ),
    ),
    AgentStarterQuestion(
        key="selective_memory_required",
        goal=AgentStarterGoal.PERSONAL,
        prompt=(
            "Must stored memory support selective inspection, "
            "editing, or deletion?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Selective memory requirements can change the "
            "acceptable memory architecture."
        ),
    ),
    AgentStarterQuestion(
        key="indefinite_all_conversation_retention_required",
        goal=AgentStarterGoal.PERSONAL,
        prompt=(
            "Must every conversation be retained indefinitely?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Retention requirements can change the suitability "
            "of persistent-memory architectures."
        ),
    ),
)


_AUTOMATION_QUESTIONS = (
    AgentStarterQuestion(
        key="workflow_deterministic",
        goal=AgentStarterGoal.AUTOMATION,
        prompt="Is the workflow fully deterministic?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "This can determine whether traditional automation "
            "is preferable to an AI agent."
        ),
    ),
    AgentStarterQuestion(
        key="destructive_or_high_impact_actions",
        goal=AgentStarterGoal.AUTOMATION,
        prompt=(
            "Can the workflow perform destructive or "
            "high-impact actions?"
        ),
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "High-impact actions can change the acceptable "
            "automation architecture and safeguards."
        ),
    ),
    AgentStarterQuestion(
        key="human_approval_required",
        goal=AgentStarterGoal.AUTOMATION,
        prompt="Is human approval required before actions execute?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Approval requirements affect acceptable autonomy."
        ),
    ),
    AgentStarterQuestion(
        key="availability_24_7_required",
        goal=AgentStarterGoal.AUTOMATION,
        prompt="Must the automation be available continuously?",
        kind=AgentStarterQuestionKind.BOOLEAN,
        reason=(
            "Continuous availability can change operational fit."
        ),
    ),
)


def _cross_cutting_questions(
    goal: AgentStarterGoal,
) -> tuple[AgentStarterQuestion, ...]:
    return (
        AgentStarterQuestion(
            key="offline_required",
            goal=goal,
            prompt="Must the agent be able to operate offline?",
            kind=AgentStarterQuestionKind.BOOLEAN,
            reason=(
                "Offline operation is a cross-cutting hard "
                "constraint that can exclude architectures "
                "requiring network connectivity."
            ),
        ),
    )


_QUESTIONS_BY_GOAL = {
    AgentStarterGoal.CODING: _CODING_QUESTIONS,
    AgentStarterGoal.KNOWLEDGE_RAG: _KNOWLEDGE_QUESTIONS,
    AgentStarterGoal.VOICE: _VOICE_QUESTIONS,
    AgentStarterGoal.AUTOMATION: _AUTOMATION_QUESTIONS,
    AgentStarterGoal.PERSONAL: _PERSONAL_QUESTIONS,
}


def _has_user_answer(
    intake: AgentStarterIntake,
    *,
    key: str,
) -> bool:
    return any(
        evidence.key == key
        and evidence.source
        in {
            EvidenceSource.DECLARED,
            EvidenceSource.UNKNOWN,
        }
        for evidence in intake.evidence
    )


def _has_declared_false(
    intake: AgentStarterIntake,
    *,
    key: str,
) -> bool:
    return any(
        evidence.key == key
        and evidence.source is EvidenceSource.DECLARED
        and evidence.value is False
        for evidence in intake.evidence
    )


def build_agent_starter_question_set(
    intake: AgentStarterIntake,
) -> AgentStarterQuestionSet:
    goal_questions = (
        *_cross_cutting_questions(intake.goal),
        *_QUESTIONS_BY_GOAL.get(
            intake.goal,
            (),
        ),
    )

    questions = [
        question
        for question in goal_questions
        if not _has_user_answer(
            intake,
            key=question.key,
        )
        and not (
            question.key == "human_approval_required"
            and _has_declared_false(
                intake,
                key="destructive_or_high_impact_actions",
            )
        )
    ]

    return AgentStarterQuestionSet(
        goal=intake.goal,
        questions=questions,
    )
