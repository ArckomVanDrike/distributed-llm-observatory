from observer.core.agent_starter_plan_builder import (
    build_agent_starter_plan,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
    ConstraintStrength,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)


def _local_only_requirement() -> AgentStarterRequirement:
    evidence = AgentStarterEvidence(
        key="source_code_must_stay_local",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    return AgentStarterRequirement(
        key="source_code_must_stay_local",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[evidence],
    )


def _candidate(
    *,
    architecture_id: str,
    recommendation: RecommendationVerdict,
) -> CandidateArchitectureAssessment:
    evidence = AgentStarterEvidence(
        key=f"{architecture_id}_assessment",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="Candidate was evaluated by Agent Starter.",
    )

    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=recommendation,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[
            "The candidate is technically feasible.",
        ],
        recommendation_reasons=[
            "The candidate was evaluated against current requirements.",
        ],
        supporting_evidence=[evidence],
    )


def test_plan_builder_preserves_all_candidate_assessments():
    requirement = _local_only_requirement()

    local_candidate = _candidate(
        architecture_id="local_coding",
        recommendation=RecommendationVerdict.POSSIBLE,
    )
    cloud_candidate = _candidate(
        architecture_id="cloud_coding",
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
    )

    result = build_agent_starter_plan(
        goal=AgentStarterGoal.CODING,
        requirements=[requirement],
        candidate_assessments=[
            local_candidate,
            cloud_candidate,
        ],
    )

    assert result.goal is AgentStarterGoal.CODING
    assert result.requirements == [requirement]
    assert result.candidate_assessments == [
        local_candidate,
        cloud_candidate,
    ]
    assert result.constraint_conflict is None


def test_plan_builder_preserves_rejected_candidates_with_explicit_conflict():
    requirement = _local_only_requirement()

    local_candidate = _candidate(
        architecture_id="local_coding",
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
    )
    cloud_candidate = _candidate(
        architecture_id="cloud_coding",
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
    )

    from schemas.agent_starter import AgentStarterConstraintConflict

    conflict = AgentStarterConstraintConflict(
        conflicting_requirements=[requirement],
        summary=(
            "No evaluated candidate satisfies the hard "
            "local-only source-code requirement."
        ),
        resolution_options=[
            "Change the hard requirement.",
            "Evaluate another local architecture.",
        ],
    )

    result = build_agent_starter_plan(
        goal=AgentStarterGoal.CODING,
        requirements=[requirement],
        candidate_assessments=[
            local_candidate,
            cloud_candidate,
        ],
        constraint_conflict=conflict,
    )

    assert result.candidate_assessments == [
        local_candidate,
        cloud_candidate,
    ]
    assert result.constraint_conflict == conflict


def _blocked_candidate(
    *,
    architecture_id: str,
    requirement: AgentStarterRequirement,
) -> CandidateArchitectureAssessment:
    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The candidate is technically feasible.",
        ],
        recommendation_reasons=[
            "A hard requirement blocks this candidate.",
        ],
        supporting_evidence=requirement.evidence,
        blocking_requirements=[requirement],
    )


def test_plan_builder_infers_conflict_from_shared_hard_blocker():
    requirement = _local_only_requirement()

    local_candidate = _blocked_candidate(
        architecture_id="local_coding",
        requirement=requirement,
    )
    cloud_candidate = _blocked_candidate(
        architecture_id="cloud_coding",
        requirement=requirement,
    )

    result = build_agent_starter_plan(
        goal=AgentStarterGoal.CODING,
        requirements=[requirement],
        candidate_assessments=[
            local_candidate,
            cloud_candidate,
        ],
    )

    assert result.candidate_assessments == [
        local_candidate,
        cloud_candidate,
    ]
    assert result.constraint_conflict is not None
    assert (
        result.constraint_conflict.conflicting_requirements
        == [requirement]
    )


def test_plan_builder_does_not_infer_conflict_from_recommendation_alone():
    requirement = _local_only_requirement()

    first = _candidate(
        architecture_id="candidate_a",
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
    )
    second = _candidate(
        architecture_id="candidate_b",
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
    )

    result = build_agent_starter_plan(
        goal=AgentStarterGoal.CODING,
        requirements=[requirement],
        candidate_assessments=[
            first,
            second,
        ],
    )

    assert result.constraint_conflict is None


def test_plan_builder_does_not_infer_conflict_from_different_blockers():
    local_only = _local_only_requirement()

    offline_evidence = AgentStarterEvidence(
        key="offline_required",
        source=EvidenceSource.DECLARED,
        value=True,
    )
    offline = AgentStarterRequirement(
        key="offline_required",
        value=True,
        strength=ConstraintStrength.HARD,
        evidence=[offline_evidence],
    )

    local_blocked = _blocked_candidate(
        architecture_id="candidate_a",
        requirement=local_only,
    )
    offline_blocked = _blocked_candidate(
        architecture_id="candidate_b",
        requirement=offline,
    )

    result = build_agent_starter_plan(
        goal=AgentStarterGoal.CODING,
        requirements=[
            local_only,
            offline,
        ],
        candidate_assessments=[
            local_blocked,
            offline_blocked,
        ],
    )

    assert result.candidate_assessments == [
        local_blocked,
        offline_blocked,
    ]
    assert result.constraint_conflict is None
