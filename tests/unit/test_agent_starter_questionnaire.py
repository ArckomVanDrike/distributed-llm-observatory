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
