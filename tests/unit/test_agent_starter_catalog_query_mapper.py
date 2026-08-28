from observer.core.agent_starter_catalog_query_mapper import (
    map_agent_starter_stack_requirement_to_catalog_query,
)
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


def test_catalog_query_mapper_preserves_stack_requirement_properties():
    evidence = AgentStarterEvidence(
        key="candidate_uses_llm",
        source=EvidenceSource.DERIVED,
        value=True,
        reason="The architecture explicitly uses an LLM.",
    )

    requirement = AgentStarterStackRequirement(
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "coding",
            "tool_use",
        ],
        required_deployment_modes=[
            "on_device",
        ],
        required_runtime="llama.cpp",
        required_pricing_class="free",
        supporting_evidence=[
            evidence,
        ],
        reason=(
            "The architecture requires a coding-capable "
            "local language model."
        ),
    )

    query = (
        map_agent_starter_stack_requirement_to_catalog_query(
            requirement
        )
    )

    assert query.component_type is AgentStarterCatalogComponentType.LLM
    assert query.required_capabilities == [
        "coding",
        "tool_use",
    ]
    assert query.required_deployment_modes == [
        "on_device",
    ]
    assert query.required_runtime == "llama.cpp"
    assert query.required_pricing_class == "free"
