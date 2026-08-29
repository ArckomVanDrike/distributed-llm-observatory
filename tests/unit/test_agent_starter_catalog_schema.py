from datetime import datetime, timezone

from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
)
from schemas.model_profile import (
    ExecutionLocation,
    ModelProfile,
)


def test_catalog_entry_keeps_recommendation_metadata_outside_model_profile():
    model = ModelProfile(
        model_id="example-7b",
        parameter_count=7_000_000_000,
        quantization="q4",
        runtime="llama.cpp",
        execution_location=ExecutionLocation.ON_DEVICE,
    )

    entry = AgentStarterCatalogEntry(
        identifier="example-7b-q4-local",
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
        privacy_implications=[
            "Can run entirely on device.",
        ],
        sources=[
            "https://example.invalid/model-card",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        model_profile=model,
    )

    assert entry.identifier == "example-7b-q4-local"
    assert (
        entry.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert entry.model_profile == model
    assert entry.capabilities == [
        "coding",
        "tool_use",
    ]
    assert entry.verified_at.tzinfo is not None

    assert "vendor" not in ModelProfile.model_fields
    assert "pricing_class" not in ModelProfile.model_fields
    assert "sources" not in ModelProfile.model_fields
    assert "verified_at" not in ModelProfile.model_fields


def test_catalog_entry_requires_at_least_one_source():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AgentStarterCatalogEntry(
            identifier="example-runtime",
            component_type=AgentStarterCatalogComponentType.RUNTIME,
            vendor="Example Vendor",
            family="Example Runtime",
            version="1.0",
            license="example-license",
            pricing_class="free",
            sources=[],
            verified_at=datetime(
                2026,
                8,
                28,
                tzinfo=timezone.utc,
            ),
        )


def test_catalog_entry_requires_timezone_aware_verified_at():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AgentStarterCatalogEntry(
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
            ),
        )


def test_catalog_entry_requires_sources_field():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AgentStarterCatalogEntry(
            identifier="example-runtime",
            component_type=AgentStarterCatalogComponentType.RUNTIME,
            vendor="Example Vendor",
            family="Example Runtime",
            version="1.0",
            license="example-license",
            pricing_class="free",
            verified_at=datetime(
                2026,
                8,
                28,
                tzinfo=timezone.utc,
            ),
        )


def test_catalog_snapshot_records_entries_and_generation_time():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogSnapshot,
    )

    entry = AgentStarterCatalogEntry(
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
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            15,
            30,
            tzinfo=timezone.utc,
        ),
        entries=[entry],
    )

    assert snapshot.snapshot_id == "catalog-2026-08-28"
    assert snapshot.entries == [entry]
    assert snapshot.generated_at.tzinfo is not None


def test_catalog_snapshot_requires_timezone_aware_generated_at():
    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogSnapshot,
    )

    with pytest.raises(ValidationError):
        AgentStarterCatalogSnapshot(
            snapshot_id="catalog-2026-08-28",
            generated_at=datetime(
                2026,
                8,
                28,
                15,
                30,
            ),
            entries=[],
        )


def test_catalog_snapshot_rejects_duplicate_entry_identifiers():
    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogSnapshot,
    )

    first = AgentStarterCatalogEntry(
        identifier="duplicate-entry",
        component_type=AgentStarterCatalogComponentType.RUNTIME,
        vendor="Example Vendor",
        family="Runtime A",
        version="1.0",
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/runtime-a",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    second = AgentStarterCatalogEntry(
        identifier="duplicate-entry",
        component_type=AgentStarterCatalogComponentType.RUNTIME,
        vendor="Example Vendor",
        family="Runtime B",
        version="2.0",
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/runtime-b",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    with pytest.raises(ValidationError):
        AgentStarterCatalogSnapshot(
            snapshot_id="catalog-2026-08-28",
            generated_at=datetime(
                2026,
                8,
                28,
                15,
                30,
                tzinfo=timezone.utc,
            ),
            entries=[
                first,
                second,
            ],
        )


def test_catalog_query_records_explicit_matching_properties():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogQuery,
    )

    query = AgentStarterCatalogQuery(
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

    assert (
        query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query.required_capabilities == [
        "coding",
        "tool_use",
    ]
    assert query.required_deployment_modes == [
        "on_device",
    ]
    assert query.required_runtime == "llama.cpp"
    assert query.required_pricing_class == "free"


def test_catalog_query_match_records_query_results_and_snapshot():
    from datetime import datetime, timezone

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogQuery,
        AgentStarterCatalogQueryMatch,
    )

    entry = AgentStarterCatalogEntry(
        identifier="coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=["coding"],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    query = AgentStarterCatalogQuery(
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=["coding"],
    )

    match = AgentStarterCatalogQueryMatch(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="catalog-2026-08-28",
        query=query,
        matched_entries=[entry],
    )

    assert match.architecture_id == "local-coding-agent"
    assert match.catalog_snapshot_id == "catalog-2026-08-28"
    assert match.query == query
    assert match.matched_entries == [entry]


def test_catalog_query_match_rejects_entries_of_different_component_type():
    from datetime import datetime, timezone

    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogQuery,
        AgentStarterCatalogQueryMatch,
    )

    runtime_entry = AgentStarterCatalogEntry(
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

    query = AgentStarterCatalogQuery(
        component_type=AgentStarterCatalogComponentType.LLM,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Matched catalog entries must have the "
            "component type requested by the query"
        ),
    ):
        AgentStarterCatalogQueryMatch(
            architecture_id="example-architecture",
            catalog_snapshot_id="catalog-2026-08-28",
            query=query,
            matched_entries=[runtime_entry],
        )


def test_catalog_query_match_allows_zero_matched_entries():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogQuery,
        AgentStarterCatalogQueryMatch,
    )

    query = AgentStarterCatalogQuery(
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "coding",
        ],
    )

    match = AgentStarterCatalogQueryMatch(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="catalog-2026-08-28",
        query=query,
        matched_entries=[],
    )

    assert match.matched_entries == []


def test_catalog_architecture_result_allows_zero_query_matches():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogArchitectureResult,
    )

    result = AgentStarterCatalogArchitectureResult(
        architecture_id="traditional-deterministic-automation",
        catalog_snapshot_id="catalog-2026-08-28",
        query_matches=[],
    )

    assert (
        result.architecture_id
        == "traditional-deterministic-automation"
    )
    assert result.catalog_snapshot_id == "catalog-2026-08-28"
    assert result.query_matches == []


def test_catalog_architecture_result_rejects_query_match_for_other_architecture():
    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogArchitectureResult,
        AgentStarterCatalogQuery,
        AgentStarterCatalogQueryMatch,
    )

    query_match = AgentStarterCatalogQueryMatch(
        architecture_id="remote-coding-agent",
        catalog_snapshot_id="catalog-2026-08-28",
        query=AgentStarterCatalogQuery(
            component_type=AgentStarterCatalogComponentType.LLM,
            required_capabilities=["coding"],
        ),
        matched_entries=[],
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Catalog architecture result may contain only "
            "query matches for the same architecture"
        ),
    ):
        AgentStarterCatalogArchitectureResult(
            architecture_id="local-coding-agent",
            catalog_snapshot_id="catalog-2026-08-28",
            query_matches=[query_match],
        )


def test_catalog_architecture_result_rejects_query_match_from_other_snapshot():
    import pytest
    from pydantic import ValidationError

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogArchitectureResult,
        AgentStarterCatalogQuery,
        AgentStarterCatalogQueryMatch,
    )

    query_match = AgentStarterCatalogQueryMatch(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="catalog-old",
        query=AgentStarterCatalogQuery(
            component_type=AgentStarterCatalogComponentType.LLM,
            required_capabilities=["coding"],
        ),
        matched_entries=[],
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Catalog architecture result may contain only "
            "query matches from the same catalog snapshot"
        ),
    ):
        AgentStarterCatalogArchitectureResult(
            architecture_id="local-coding-agent",
            catalog_snapshot_id="catalog-current",
            query_matches=[query_match],
        )


def test_catalog_entry_retains_extended_recommendation_metadata():
    from datetime import datetime, timezone

    entry = AgentStarterCatalogEntry(
        identifier="example-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=["coding"],
        resource_profile={
            "memory_band": "medium",
            "accelerators": ["cpu", "cuda"],
        },
        context_characteristics={
            "context_window_tokens": 32768,
        },
        language_support=[
            "en",
            "es",
            "it",
        ],
        streaming_support=True,
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    assert entry.resource_profile == {
        "memory_band": "medium",
        "accelerators": ["cpu", "cuda"],
    }
    assert entry.context_characteristics == {
        "context_window_tokens": 32768,
    }
    assert entry.language_support == [
        "en",
        "es",
        "it",
    ]
    assert entry.streaming_support is True


def _catalog_cost_metadata_payload(
    **overrides,
):
    payload = {
        "schema_version": "0.1",
        "identifier": "example-model",
        "component_type": "llm",
        "vendor": "Example",
        "family": "Example",
        "version": "1.0",
        "capabilities": [
            "text_generation",
        ],
        "deployment_modes": [
            "on_device",
        ],
        "supported_runtimes": [
            "ollama",
        ],
        "resource_profile": {},
        "context_characteristics": {},
        "language_support": [
            "en",
        ],
        "streaming_support": True,
        "license": "example-license",
        "pricing_class": "free",
        "privacy_implications": [],
        "sources": [
            "https://example.com/model",
        ],
        "verified_at": (
            "2026-08-29T20:00:00+00:00"
        ),
    }

    payload.update(overrides)

    return payload


def test_catalog_cost_metadata_is_backward_compatible_with_v0_1():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogEntry,
    )

    entry = AgentStarterCatalogEntry.model_validate(
        _catalog_cost_metadata_payload()
    )

    assert entry.schema_version == "0.1"
    assert entry.release_status.value == "unknown"
    assert entry.license_cost.value == "unknown"

    assert [
        pricing.value
        for pricing in entry.access_pricing
    ] == [
        "unknown",
    ]

    assert entry.pricing_notes is None


def test_catalog_cost_metadata_represents_free_stable_component():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogEntry,
    )

    entry = AgentStarterCatalogEntry.model_validate(
        _catalog_cost_metadata_payload(
            schema_version="0.2",
            release_status="stable",
            license_cost="free",
            access_pricing=[
                "free",
            ],
            pricing_notes=(
                "The component can be obtained without "
                "a paid license or service subscription."
            ),
        )
    )

    assert entry.schema_version == "0.2"
    assert entry.release_status.value == "stable"
    assert entry.license_cost.value == "free"

    assert [
        pricing.value
        for pricing in entry.access_pricing
    ] == [
        "free",
    ]


def test_catalog_cost_metadata_represents_paid_service_access():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogEntry,
    )

    entry = AgentStarterCatalogEntry.model_validate(
        _catalog_cost_metadata_payload(
            schema_version="0.2",
            identifier="provider-api-model",
            deployment_modes=[
                "remote",
            ],
            release_status="stable",
            license="proprietary",
            pricing_class="paid",
            license_cost="paid",
            access_pricing=[
                "usage_based",
            ],
            pricing_notes=(
                "Remote access is billed according "
                "to provider usage."
            ),
        )
    )

    assert entry.license_cost.value == "paid"

    assert [
        pricing.value
        for pricing in entry.access_pricing
    ] == [
        "usage_based",
    ]


def test_catalog_cost_metadata_represents_experimental_preview():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogEntry,
    )

    entry = AgentStarterCatalogEntry.model_validate(
        _catalog_cost_metadata_payload(
            schema_version="0.2",
            identifier="experimental-model",
            release_status="experimental_preview",
            license_cost="restricted",
            access_pricing=[
                "provider_dependent",
            ],
            pricing_notes=(
                "Pricing depends on the selected "
                "deployment or provider."
            ),
        )
    )

    assert (
        entry.release_status.value
        == "experimental_preview"
    )
    assert entry.license_cost.value == "restricted"


def test_catalog_snapshot_accepts_v0_2_entries():
    from datetime import datetime, timezone

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogEntry,
        AgentStarterCatalogSnapshot,
    )

    entry = AgentStarterCatalogEntry.model_validate(
        _catalog_cost_metadata_payload(
            schema_version="0.2",
            release_status="stable",
            license_cost="free",
            access_pricing=[
                "free",
            ],
        )
    )

    snapshot = AgentStarterCatalogSnapshot(
        schema_version="0.2",
        snapshot_id="agent-starter-catalog-v0-2",
        generated_at=datetime(
            2026,
            8,
            29,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        entries=[
            entry,
        ],
    )

    assert snapshot.schema_version == "0.2"
    assert snapshot.entries == [
        entry,
    ]
