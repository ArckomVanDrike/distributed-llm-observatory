import pytest
from pydantic import ValidationError

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterPlan,
    CandidateArchitectureAssessment,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogArchitectureResult,
)
from schemas.agent_starter_result import (
    AgentStarterCatalogMatchingResult,
)
from schemas.agent_starter_stack import (
    AgentStarterConcreteStack,
)


def _assessment(
    architecture_id: str,
) -> CandidateArchitectureAssessment:
    return CandidateArchitectureAssessment(
        architecture_id=architecture_id,
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.MEDIUM,
        technical_reasons=[
            "The architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The architecture is a possible option.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The architecture requires "
                    "a language model."
                ),
            ),
        ],
    )


def _catalog_result() -> AgentStarterCatalogMatchingResult:
    assessments = [
        _assessment("local-coding-agent"),
        _assessment("cloud-coding-agent"),
    ]

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=assessments,
    )

    return AgentStarterCatalogMatchingResult(
        plan=plan,
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        architecture_results=[
            AgentStarterCatalogArchitectureResult(
                architecture_id="local-coding-agent",
                catalog_snapshot_id=(
                    "agent-starter-catalog-v0-1"
                ),
                query_matches=[],
            ),
            AgentStarterCatalogArchitectureResult(
                architecture_id="cloud-coding-agent",
                catalog_snapshot_id=(
                    "agent-starter-catalog-v0-1"
                ),
                query_matches=[],
            ),
        ],
    )


def test_concrete_stack_resolution_records_all_stacks_in_order():
    from schemas.agent_starter_result import (
        AgentStarterConcreteStackResolution,
    )

    catalog_result = _catalog_result()

    stacks = [
        AgentStarterConcreteStack(
            architecture_id="local-coding-agent",
            catalog_snapshot_id="agent-starter-catalog-v0-1",
        ),
        AgentStarterConcreteStack(
            architecture_id="cloud-coding-agent",
            catalog_snapshot_id="agent-starter-catalog-v0-1",
        ),
    ]

    resolution = AgentStarterConcreteStackResolution(
        catalog_result=catalog_result,
        stacks=stacks,
    )

    assert resolution.catalog_result == catalog_result
    assert resolution.stacks == stacks


def test_concrete_stack_resolution_rejects_missing_or_reordered_stack():
    from schemas.agent_starter_result import (
        AgentStarterConcreteStackResolution,
    )

    catalog_result = _catalog_result()

    with pytest.raises(
        ValidationError,
        match="correspond exactly",
    ):
        AgentStarterConcreteStackResolution(
            catalog_result=catalog_result,
            stacks=[
                AgentStarterConcreteStack(
                    architecture_id="cloud-coding-agent",
                    catalog_snapshot_id=(
                        "agent-starter-catalog-v0-1"
                    ),
                ),
                AgentStarterConcreteStack(
                    architecture_id="local-coding-agent",
                    catalog_snapshot_id=(
                        "agent-starter-catalog-v0-1"
                    ),
                ),
            ],
        )


def test_concrete_stack_resolution_rejects_other_catalog_snapshot():
    from schemas.agent_starter_result import (
        AgentStarterConcreteStackResolution,
    )

    catalog_result = _catalog_result()

    with pytest.raises(
        ValidationError,
        match="catalog snapshot",
    ):
        AgentStarterConcreteStackResolution(
            catalog_result=catalog_result,
            stacks=[
                AgentStarterConcreteStack(
                    architecture_id="local-coding-agent",
                    catalog_snapshot_id="catalog-other",
                ),
                AgentStarterConcreteStack(
                    architecture_id="cloud-coding-agent",
                    catalog_snapshot_id="catalog-other",
                ),
            ],
        )
