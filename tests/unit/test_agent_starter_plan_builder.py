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
