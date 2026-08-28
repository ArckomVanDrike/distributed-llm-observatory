from schemas.agent_starter import (
    AgentStarterEvidence,
    EvidenceSource,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
)
from schemas.agent_starter_stack import (
    AgentStarterStackRequirement,
)


def test_stack_requirement_retains_component_properties_and_evidence():
    evidence = AgentStarterEvidence(
        key="source_code_remote_processing",
        source=EvidenceSource.DERIVED,
        value=False,
        reason=(
            "Source code remains inside the "
            "user-controlled environment."
        ),
    )

    requirement = AgentStarterStackRequirement(
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "coding",
        ],
        supporting_evidence=[
            evidence,
        ],
        reason=(
            "The coding architecture requires a "
            "coding-capable language model."
        ),
    )

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
        evidence,
    ]


def test_stack_requirement_requires_supporting_evidence():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(
        ValidationError,
        match="supporting_evidence",
    ):
        AgentStarterStackRequirement(
            component_type=AgentStarterCatalogComponentType.LLM,
            required_capabilities=[
                "coding",
            ],
            supporting_evidence=[],
            reason=(
                "The coding architecture requires a "
                "coding-capable language model."
            ),
        )
