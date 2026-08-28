from observer.core.agent_starter_assessment_orchestrator import (
    assess_agent_starter_candidates,
)
from observer.core.agent_starter_input_orchestrator import (
    prepare_agent_starter_input,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    EvidenceSource,
    RecommendationVerdict,
    TechnicalFeasibility,
)


def test_assessment_orchestrator_computes_feasibility_before_decision():
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

    prepared = prepare_agent_starter_input(intake)

    assessments = assess_agent_starter_candidates(
        prepared=prepared,
    )

    session_only = next(
        assessment
        for assessment in assessments
        if (
            assessment.architecture_id
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


def test_assessment_orchestrator_preserves_all_candidates_and_order():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
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

    prepared = prepare_agent_starter_input(intake)
    candidates = generate_agent_starter_candidates(prepared)

    assessments = assess_agent_starter_candidates(
        prepared=prepared,
    )

    assert [
        assessment.architecture_id
        for assessment in assessments
    ] == [
        candidate.architecture_id
        for candidate in candidates
    ]

    assert len(assessments) == len(candidates)


def test_assessment_orchestrator_preserves_technical_feasibility_reasons():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from observer.core.agent_starter_feasibility_evaluator import (
        evaluate_agent_starter_technical_feasibility,
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

    prepared = prepare_agent_starter_input(intake)
    candidates = generate_agent_starter_candidates(prepared)

    candidate = next(
        candidate
        for candidate in candidates
        if (
            candidate.architecture_id
            == "session-only-personal-assistant"
        )
    )

    feasibility = evaluate_agent_starter_technical_feasibility(
        prepared=prepared,
        candidate=candidate,
    )

    assessments = assess_agent_starter_candidates(
        prepared=prepared,
    )

    assessment = next(
        assessment
        for assessment in assessments
        if assessment.architecture_id == candidate.architecture_id
    )

    assert assessment.technical_reasons == feasibility.reasons


def test_assessment_orchestrator_preserves_technical_supporting_evidence():
    from observer.core.agent_starter_candidate_generator import (
        generate_agent_starter_candidates,
    )
    from observer.core.agent_starter_feasibility_evaluator import (
        evaluate_agent_starter_technical_feasibility,
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

    prepared = prepare_agent_starter_input(intake)
    candidates = generate_agent_starter_candidates(prepared)

    candidate = next(
        candidate
        for candidate in candidates
        if (
            candidate.architecture_id
            == "session-only-personal-assistant"
        )
    )

    feasibility = evaluate_agent_starter_technical_feasibility(
        prepared=prepared,
        candidate=candidate,
    )

    assessments = assess_agent_starter_candidates(
        prepared=prepared,
    )

    assessment = next(
        assessment
        for assessment in assessments
        if assessment.architecture_id == candidate.architecture_id
    )

    for evidence in feasibility.supporting_evidence:
        assert evidence in assessment.supporting_evidence
