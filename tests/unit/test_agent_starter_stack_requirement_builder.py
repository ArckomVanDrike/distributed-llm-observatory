from observer.core.agent_starter_stack_requirement_builder import (
    build_agent_starter_stack_requirements,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    CandidateArchitectureAssessment,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
)


def test_stack_requirement_builder_maps_coding_llm_requirement():
    llm_evidence = AgentStarterEvidence(
        key="candidate_uses_llm",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The coding-agent architecture uses an LLM "
            "for coding assistance."
        ),
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The coding architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The coding architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            llm_evidence,
        ],
    )

    requirements = build_agent_starter_stack_requirements(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
    )

    assert len(requirements) == 1

    requirement = requirements[0]

    assert (
        requirement.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert requirement.required_capabilities == [
        "coding",
    ]
    assert requirement.required_deployment_modes == []
    assert requirement.required_runtime is None
    assert requirement.required_pricing_class is None
    assert requirement.supporting_evidence == [
        llm_evidence,
    ]


def test_stack_requirement_builder_rejects_coding_without_llm_evidence():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "LLM usage is not established.",
        ],
        recommendation_reasons=[
            "The stack cannot be mapped safely.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="unrelated_evidence",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The assessment contains evidence, "
                    "but not LLM-usage evidence."
                ),
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Coding stack mapping requires exactly one "
            "candidate_uses_llm evidence value equal to true"
        ),
    ):
        build_agent_starter_stack_requirements(
            goal=AgentStarterGoal.CODING,
            assessment=assessment,
        )


def test_stack_requirement_builder_rejects_coding_without_llm_usage():
    import pytest

    assessment = CandidateArchitectureAssessment(
        architecture_id="coding-without-llm",
        technical_feasibility=TechnicalFeasibility.UNKNOWN,
        recommendation=RecommendationVerdict.NOT_RECOMMENDED,
        confidence=RecommendationConfidence.LIMITED,
        technical_reasons=[
            "The candidate does not use an LLM.",
        ],
        recommendation_reasons=[
            "The coding LLM stack requirement does not apply.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "The candidate explicitly does not use an LLM."
                ),
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Coding stack mapping requires exactly one "
            "candidate_uses_llm evidence value equal to true"
        ),
    ):
        build_agent_starter_stack_requirements(
            goal=AgentStarterGoal.CODING,
            assessment=assessment,
        )
