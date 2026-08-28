from datetime import datetime, timezone

from observer.core.agent_starter_catalog_matcher import (
    match_agent_starter_catalog_entries,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
    AgentStarterCatalogSnapshot,
)


def _entry(
    *,
    identifier: str,
    capabilities: list[str],
) -> AgentStarterCatalogEntry:
    return AgentStarterCatalogEntry(
        identifier=identifier,
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=capabilities,
        license="example-license",
        pricing_class="free",
        sources=[
            f"https://example.invalid/{identifier}",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )


def test_catalog_matcher_returns_all_capability_matches_in_snapshot_order():
    first_match = _entry(
        identifier="coding-model-a",
        capabilities=[
            "coding",
            "tool_use",
            "general_chat",
        ],
    )
    non_match = _entry(
        identifier="coding-model-without-tools",
        capabilities=[
            "coding",
        ],
    )
    second_match = _entry(
        identifier="coding-model-b",
        capabilities=[
            "tool_use",
            "coding",
        ],
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="test-catalog",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[
            first_match,
            non_match,
            second_match,
        ],
    )

    matches = match_agent_starter_catalog_entries(
        snapshot=snapshot,
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "coding",
            "tool_use",
        ],
    )

    assert [
        entry.identifier
        for entry in matches
    ] == [
        "coding-model-a",
        "coding-model-b",
    ]


def test_catalog_matcher_does_not_cross_component_types():
    llm = _entry(
        identifier="coding-llm",
        capabilities=[
            "coding",
            "tool_use",
        ],
    )

    runtime = AgentStarterCatalogEntry(
        identifier="coding-runtime",
        component_type=AgentStarterCatalogComponentType.RUNTIME,
        vendor="Example Vendor",
        family="Example Runtime",
        version="1.0",
        capabilities=[
            "coding",
            "tool_use",
        ],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/coding-runtime",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="test-catalog",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[
            runtime,
            llm,
        ],
    )

    matches = match_agent_starter_catalog_entries(
        snapshot=snapshot,
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "coding",
            "tool_use",
        ],
    )

    assert matches == [llm]


def test_catalog_matcher_empty_capabilities_returns_all_entries_of_type():
    first = _entry(
        identifier="general-model",
        capabilities=[
            "general_chat",
        ],
    )
    second = _entry(
        identifier="coding-model",
        capabilities=[
            "coding",
        ],
    )

    runtime = AgentStarterCatalogEntry(
        identifier="example-runtime",
        component_type=AgentStarterCatalogComponentType.RUNTIME,
        vendor="Example Vendor",
        family="Example Runtime",
        version="1.0",
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/runtime",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="test-catalog",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[
            first,
            runtime,
            second,
        ],
    )

    matches = match_agent_starter_catalog_entries(
        snapshot=snapshot,
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[],
    )

    assert matches == [
        first,
        second,
    ]


def test_catalog_matcher_filters_by_required_deployment_mode():
    local = AgentStarterCatalogEntry(
        identifier="local-coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=[
            "coding",
            "tool_use",
        ],
        deployment_modes=[
            "on_device",
        ],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/local-coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    remote = AgentStarterCatalogEntry(
        identifier="remote-coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=[
            "coding",
            "tool_use",
        ],
        deployment_modes=[
            "remote",
        ],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/remote-coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="test-catalog",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[
            remote,
            local,
        ],
    )

    matches = match_agent_starter_catalog_entries(
        snapshot=snapshot,
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "coding",
            "tool_use",
        ],
        required_deployment_modes=[
            "on_device",
        ],
    )

    assert matches == [local]


def test_catalog_matcher_filters_by_required_runtime():
    llama_cpp = AgentStarterCatalogEntry(
        identifier="local-llama-coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=[
            "coding",
            "tool_use",
        ],
        deployment_modes=[
            "on_device",
        ],
        supported_runtimes=[
            "llama.cpp",
        ],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/local-llama-coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    vllm = AgentStarterCatalogEntry(
        identifier="local-vllm-coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=[
            "coding",
            "tool_use",
        ],
        deployment_modes=[
            "on_device",
        ],
        supported_runtimes=[
            "vllm",
        ],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/local-vllm-coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="test-catalog",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[
            vllm,
            llama_cpp,
        ],
    )

    matches = match_agent_starter_catalog_entries(
        snapshot=snapshot,
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "coding",
            "tool_use",
        ],
        required_deployment_modes=[
            "on_device",
        ],
        required_runtime="llama.cpp",
    )

    assert matches == [llama_cpp]


def test_catalog_matcher_filters_by_required_pricing_class():
    free_model = AgentStarterCatalogEntry(
        identifier="free-coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=[
            "coding",
            "tool_use",
        ],
        deployment_modes=[
            "on_device",
        ],
        supported_runtimes=[
            "llama.cpp",
        ],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/free-coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    paid_model = AgentStarterCatalogEntry(
        identifier="paid-coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=[
            "coding",
            "tool_use",
        ],
        deployment_modes=[
            "on_device",
        ],
        supported_runtimes=[
            "llama.cpp",
        ],
        license="example-license",
        pricing_class="paid",
        sources=[
            "https://example.invalid/paid-coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="test-catalog",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[
            paid_model,
            free_model,
        ],
    )

    matches = match_agent_starter_catalog_entries(
        snapshot=snapshot,
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
    )

    assert matches == [free_model]
