from observer.core.agent_starter_pipeline import (
    run_agent_starter_pipeline,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    EvidenceSource,
    RecommendationVerdict,
    TechnicalFeasibility,
)


def test_pipeline_builds_plan_from_intake():
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

    plan = run_agent_starter_pipeline(
        intake=intake,
    )

    assert plan.goal is AgentStarterGoal.PERSONAL

    assert [
        candidate.architecture_id
        for candidate in plan.candidate_assessments
    ] == [
        "session-only-personal-assistant",
        "opaque-persistent-memory-assistant",
        "controlled-persistent-memory-assistant",
    ]

    session_only = next(
        candidate
        for candidate in plan.candidate_assessments
        if (
            candidate.architecture_id
            == "session-only-personal-assistant"
        )
    )

    assert (
        session_only.technical_feasibility
        is TechnicalFeasibility.NOT_FEASIBLE
    )
    assert (
        session_only.recommendation
        is RecommendationVerdict.NOT_RECOMMENDED
    )


def test_pipeline_propagates_candidate_specific_compatibility():
    from schemas.compatibility import (
        AssessmentBasis,
        CompatibilityAssessment,
        CompatibilityVerdict,
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

    compatibility = CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.COMPATIBLE,
        summary=(
            "The local coding candidate has sufficient "
            "technical headroom."
        ),
        confidence=0.6,
    )

    plan = run_agent_starter_pipeline(
        intake=intake,
        compatibility_by_architecture={
            "local-coding-agent": compatibility,
        },
    )

    local = next(
        candidate
        for candidate in plan.candidate_assessments
        if candidate.architecture_id == "local-coding-agent"
    )

    remote = next(
        candidate
        for candidate in plan.candidate_assessments
        if candidate.architecture_id == "remote-coding-agent"
    )

    assert (
        local.technical_feasibility
        is TechnicalFeasibility.FEASIBLE
    )
    assert (
        remote.technical_feasibility
        is TechnicalFeasibility.UNKNOWN
    )

    assert any(
        evidence.key == "candidate_compatibility_verdict"
        for evidence in local.supporting_evidence
    )
