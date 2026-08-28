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
