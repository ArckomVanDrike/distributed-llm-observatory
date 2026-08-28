import json
from pathlib import Path

from observer.core.agent_starter_catalog_bank import (
    AgentStarterCatalogBank,
)


def test_catalog_bank_loads_valid_snapshot(
    tmp_path: Path,
):
    path = tmp_path / "catalog-v0-1.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "snapshot_id": "catalog-v0-1",
                "generated_at": "2026-08-28T00:00:00+00:00",
                "entries": [
                    {
                        "schema_version": "0.1",
                        "identifier": "example-model",
                        "component_type": "llm",
                        "vendor": "Example Vendor",
                        "family": "Example",
                        "version": "1.0",
                        "capabilities": [
                            "coding",
                        ],
                        "license": "example-license",
                        "pricing_class": "free",
                        "sources": [
                            "https://example.invalid/model",
                        ],
                        "verified_at": (
                            "2026-08-28T00:00:00+00:00"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    bank = AgentStarterCatalogBank(
        root=tmp_path,
    )

    snapshot = bank.load_snapshot(
        "catalog-v0-1.json",
    )

    assert snapshot.snapshot_id == "catalog-v0-1"
    assert [
        entry.identifier
        for entry in snapshot.entries
    ] == [
        "example-model",
    ]


def test_catalog_bank_wraps_missing_file_error(
    tmp_path: Path,
):
    import pytest

    from observer.core.agent_starter_catalog_bank import (
        AgentStarterCatalogBankError,
    )

    bank = AgentStarterCatalogBank(
        root=tmp_path,
    )

    with pytest.raises(
        AgentStarterCatalogBankError,
        match="Unable to read catalog snapshot",
    ):
        bank.load_snapshot(
            "missing-catalog.json",
        )


def test_catalog_bank_wraps_invalid_json_error(
    tmp_path: Path,
):
    import pytest

    from observer.core.agent_starter_catalog_bank import (
        AgentStarterCatalogBankError,
    )

    path = tmp_path / "invalid-catalog.json"
    path.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    bank = AgentStarterCatalogBank(
        root=tmp_path,
    )

    with pytest.raises(
        AgentStarterCatalogBankError,
        match="Invalid JSON in catalog snapshot",
    ):
        bank.load_snapshot(
            "invalid-catalog.json",
        )


def test_catalog_bank_wraps_invalid_snapshot_schema_error(
    tmp_path: Path,
):
    import pytest

    from observer.core.agent_starter_catalog_bank import (
        AgentStarterCatalogBankError,
    )

    path = tmp_path / "invalid-schema.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "snapshot_id": "",
                "generated_at": "not-a-datetime",
                "entries": [],
            }
        ),
        encoding="utf-8",
    )

    bank = AgentStarterCatalogBank(
        root=tmp_path,
    )

    with pytest.raises(
        AgentStarterCatalogBankError,
        match="Invalid catalog snapshot",
    ):
        bank.load_snapshot(
            "invalid-schema.json",
        )
