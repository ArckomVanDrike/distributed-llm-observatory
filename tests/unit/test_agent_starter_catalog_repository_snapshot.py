from pathlib import Path

from observer.core.agent_starter_catalog_bank import (
    AgentStarterCatalogBank,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
)


def test_repository_catalog_v0_1_loads_as_explicit_snapshot():
    bank = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    )

    snapshot = bank.load_snapshot(
        "catalog-v0-1.json",
    )

    assert snapshot.snapshot_id == "agent-starter-catalog-v0-1"

    assert [
        entry.identifier
        for entry in snapshot.entries
    ] == [
        "qwen2.5-coder-7b-instruct",
        "ollama-v0.33.1",
        "whisper.cpp-v1.9.2",
        "kokoro-82m-v1.0",
    ]

    assert [
        entry.component_type
        for entry in snapshot.entries
    ] == [
        AgentStarterCatalogComponentType.LLM,
        AgentStarterCatalogComponentType.RUNTIME,
        AgentStarterCatalogComponentType.STT,
        AgentStarterCatalogComponentType.TTS,
    ]
