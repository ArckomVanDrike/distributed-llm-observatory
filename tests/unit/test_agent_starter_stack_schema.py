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


def _concrete_stack_catalog_entry(
    identifier: str,
):
    from datetime import datetime, timezone

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogComponentType,
        AgentStarterCatalogEntry,
    )

    return AgentStarterCatalogEntry(
        identifier=identifier,
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="test-vendor",
        family="test-family",
        version="1.0",
        license="test-license",
        pricing_class="free",
        sources=[
            "https://example.com/catalog-entry",
        ],
        verified_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
    )


def _concrete_stack_requirement():
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

    evidence = AgentStarterEvidence(
        key="candidate_uses_llm",
        source=EvidenceSource.DERIVED,
        value=True,
        reason=(
            "The architecture requires a language model."
        ),
    )

    return AgentStarterStackRequirement(
        component_type=AgentStarterCatalogComponentType.LLM,
        supporting_evidence=[
            evidence,
        ],
        reason=(
            "The architecture requires a language model."
        ),
    )


def test_concrete_stack_component_records_unique_selected_match():
    from schemas.agent_starter_stack import (
        AgentStarterConcreteStackComponent,
    )

    requirement = _concrete_stack_requirement()
    entry = _concrete_stack_catalog_entry("model-a")

    component = AgentStarterConcreteStackComponent(
        requirement=requirement,
        matched_entries=[
            entry,
        ],
        selected_entry=entry,
    )

    assert component.requirement == requirement
    assert component.matched_entries == [entry]
    assert component.selected_entry == entry


def test_concrete_stack_component_preserves_zero_match():
    from schemas.agent_starter_stack import (
        AgentStarterConcreteStackComponent,
    )

    component = AgentStarterConcreteStackComponent(
        requirement=_concrete_stack_requirement(),
        matched_entries=[],
        selected_entry=None,
    )

    assert component.matched_entries == []
    assert component.selected_entry is None


def test_concrete_stack_component_rejects_arbitrary_multiple_match_selection():
    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter_stack import (
        AgentStarterConcreteStackComponent,
    )

    first = _concrete_stack_catalog_entry("model-a")
    second = _concrete_stack_catalog_entry("model-b")

    with pytest.raises(
        ValidationError,
        match="multiple catalog matches",
    ):
        AgentStarterConcreteStackComponent(
            requirement=_concrete_stack_requirement(),
            matched_entries=[
                first,
                second,
            ],
            selected_entry=first,
        )


def test_concrete_stack_records_architecture_snapshot_and_components():
    from schemas.agent_starter_stack import (
        AgentStarterConcreteStack,
        AgentStarterConcreteStackComponent,
    )

    requirement = _concrete_stack_requirement()
    entry = _concrete_stack_catalog_entry("model-a")

    component = AgentStarterConcreteStackComponent(
        requirement=requirement,
        matched_entries=[
            entry,
        ],
        selected_entry=entry,
    )

    stack = AgentStarterConcreteStack(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        components=[
            component,
        ],
    )

    assert stack.architecture_id == "local-coding-agent"
    assert (
        stack.catalog_snapshot_id
        == "agent-starter-catalog-v0-1"
    )
    assert stack.components == [component]


def test_concrete_stack_component_preserves_non_matching_result_classes():
    from schemas.agent_starter_stack import (
        AgentStarterConcreteStackComponent,
    )

    indeterminate = _concrete_stack_catalog_entry(
        "unknown-cost-model"
    )
    excluded = _concrete_stack_catalog_entry(
        "paid-service-model"
    )

    component = AgentStarterConcreteStackComponent(
        requirement=_concrete_stack_requirement(),
        matched_entries=[],
        indeterminate_entries=[
            indeterminate,
        ],
        constraint_excluded_entries=[
            excluded,
        ],
        selected_entry=None,
    )

    assert component.matched_entries == []
    assert component.indeterminate_entries == [
        indeterminate,
    ]
    assert component.constraint_excluded_entries == [
        excluded,
    ]
    assert component.selected_entry is None


def test_concrete_stack_component_rejects_matched_indeterminate_overlap():
    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter_stack import (
        AgentStarterConcreteStackComponent,
    )

    entry = _concrete_stack_catalog_entry(
        "duplicate-model"
    )

    with pytest.raises(ValidationError):
        AgentStarterConcreteStackComponent(
            requirement=_concrete_stack_requirement(),
            matched_entries=[
                entry,
            ],
            indeterminate_entries=[
                entry,
            ],
            selected_entry=None,
        )


def test_concrete_stack_component_rejects_indeterminate_excluded_overlap():
    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter_stack import (
        AgentStarterConcreteStackComponent,
    )

    entry = _concrete_stack_catalog_entry(
        "duplicate-model"
    )

    with pytest.raises(ValidationError):
        AgentStarterConcreteStackComponent(
            requirement=_concrete_stack_requirement(),
            matched_entries=[],
            indeterminate_entries=[
                entry,
            ],
            constraint_excluded_entries=[
                entry,
            ],
            selected_entry=None,
        )
