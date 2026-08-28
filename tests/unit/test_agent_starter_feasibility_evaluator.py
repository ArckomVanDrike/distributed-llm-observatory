import pytest

from schemas.agent_starter import (
    AgentStarterCandidateArchitecture,
    AgentStarterGoal,
    AgentStarterPreparedInput,
    EvidenceSource,
    TechnicalFeasibility,
)
from schemas.hardware import (
    DeviceClass,
    HardwareProfile,
    HardwareProfileSource,
)


def test_feasibility_is_unknown_without_technical_basis():
    from observer.core.agent_starter_feasibility_evaluator import (
        evaluate_agent_starter_technical_feasibility,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )
    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assessment = evaluate_agent_starter_technical_feasibility(
        prepared=prepared,
        candidate=candidate,
    )

    assert assessment.architecture_id == "local-coding-agent"
    assert assessment.goal is AgentStarterGoal.CODING
    assert (
        assessment.technical_feasibility
        is TechnicalFeasibility.UNKNOWN
    )
    assert assessment.reasons
    assert assessment.supporting_evidence == []


def test_hardware_profile_alone_does_not_imply_feasibility():
    from observer.core.agent_starter_feasibility_evaluator import (
        evaluate_agent_starter_technical_feasibility,
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=16 * 1024**3,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
        hardware_profile=hardware,
    )
    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assessment = evaluate_agent_starter_technical_feasibility(
        prepared=prepared,
        candidate=candidate,
    )

    assert (
        assessment.technical_feasibility
        is TechnicalFeasibility.UNKNOWN
    )
    assert assessment.supporting_evidence == []
    assert assessment.reasons


def test_missing_technical_information_never_defaults_to_not_feasible():
    from observer.core.agent_starter_feasibility_evaluator import (
        evaluate_agent_starter_technical_feasibility,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.VOICE,
    )
    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-voice-pipeline",
        goal=AgentStarterGoal.VOICE,
    )

    assessment = evaluate_agent_starter_technical_feasibility(
        prepared=prepared,
        candidate=candidate,
    )

    assert (
        assessment.technical_feasibility
        is not TechnicalFeasibility.NOT_FEASIBLE
    )
    assert (
        assessment.technical_feasibility
        is TechnicalFeasibility.UNKNOWN
    )


def test_feasibility_rejects_goal_mismatch():
    from observer.core.agent_starter_feasibility_evaluator import (
        evaluate_agent_starter_technical_feasibility,
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )
    candidate = AgentStarterCandidateArchitecture(
        architecture_id="cloud-voice-pipeline",
        goal=AgentStarterGoal.VOICE,
    )

    with pytest.raises(
        ValueError,
        match="goal",
    ):
        evaluate_agent_starter_technical_feasibility(
            prepared=prepared,
            candidate=candidate,
        )


@pytest.mark.parametrize(
    (
        "compatibility_verdict",
        "expected_feasibility",
    ),
    [
        (
            "compatible",
            TechnicalFeasibility.FEASIBLE,
        ),
        (
            "constrained",
            TechnicalFeasibility.LIMITED,
        ),
        (
            "not_recommended",
            TechnicalFeasibility.LIMITED,
        ),
        (
            "unknown",
            TechnicalFeasibility.UNKNOWN,
        ),
    ],
)
def test_feasibility_uses_compatibility_assessment_as_technical_basis(
    compatibility_verdict,
    expected_feasibility,
):
    from observer.core.agent_starter_feasibility_evaluator import (
        evaluate_agent_starter_technical_feasibility,
    )
    from schemas.compatibility import (
        AssessmentBasis,
        CompatibilityAssessment,
        CompatibilityVerdict,
    )

    compatibility = CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict(compatibility_verdict),
        summary="Candidate-specific compatibility assessment.",
        reasons=[
            "Compatibility was evaluated from known technical inputs.",
        ],
    )

    prepared = AgentStarterPreparedInput(
        goal=AgentStarterGoal.CODING,
    )
    candidate = AgentStarterCandidateArchitecture(
        architecture_id="local-coding-agent",
        goal=AgentStarterGoal.CODING,
    )

    assessment = evaluate_agent_starter_technical_feasibility(
        prepared=prepared,
        candidate=candidate,
        compatibility_assessment=compatibility,
    )

    assert (
        assessment.technical_feasibility
        is expected_feasibility
    )

    assert assessment.reasons == [
        "Candidate-specific compatibility assessment.",
        "Compatibility was evaluated from known technical inputs.",
    ]

    assert len(assessment.supporting_evidence) == 1

    evidence = assessment.supporting_evidence[0]

    assert evidence.key == "candidate_compatibility_verdict"
    assert evidence.source is EvidenceSource.DERIVED
    assert evidence.value == compatibility_verdict
    assert evidence.reason == compatibility.summary


def test_not_recommended_compatibility_never_becomes_not_feasible():
    from observer.core.agent_starter_feasibility_evaluator import (
        evaluate_agent_starter_technical_feasibility,
    )
    from schemas.compatibility import (
        AssessmentBasis,
        CompatibilityAssessment,
        CompatibilityVerdict,
    )

    compatibility = CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.NOT_RECOMMENDED,
        summary="Estimated local headroom is insufficiently comfortable.",
    )

    assessment = evaluate_agent_starter_technical_feasibility(
        prepared=AgentStarterPreparedInput(
            goal=AgentStarterGoal.CODING,
        ),
        candidate=AgentStarterCandidateArchitecture(
            architecture_id="local-coding-agent",
            goal=AgentStarterGoal.CODING,
        ),
        compatibility_assessment=compatibility,
    )

    assert (
        assessment.technical_feasibility
        is TechnicalFeasibility.LIMITED
    )
    assert (
        assessment.technical_feasibility
        is not TechnicalFeasibility.NOT_FEASIBLE
    )
