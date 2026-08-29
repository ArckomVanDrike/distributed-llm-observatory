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
    if intake.goal is not AgentStarterGoal.AUTOMATION:
        return AgentStarterQuestionSet(
            goal=intake.goal,
        )

    questions = [
        question
        for question in _AUTOMATION_QUESTIONS
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
