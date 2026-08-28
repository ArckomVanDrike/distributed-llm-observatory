from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from schemas.agent_starter_catalog import (
    AgentStarterCatalogSnapshot,
)


class AgentStarterCatalogBankError(Exception):
    """Raised when an Agent Starter catalog cannot be loaded safely."""


class AgentStarterCatalogBank:
    def __init__(
        self,
        root: Path,
    ) -> None:
        self.root = root

    def load_snapshot(
        self,
        filename: str,
    ) -> AgentStarterCatalogSnapshot:
        path = self.root / filename

        try:
            raw_text = path.read_text(
                encoding="utf-8",
            )
        except OSError as exc:
            raise AgentStarterCatalogBankError(
                f"Unable to read catalog snapshot: {path}"
            ) from exc

        try:
            raw_data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AgentStarterCatalogBankError(
                f"Invalid JSON in catalog snapshot: {path}"
            ) from exc

        try:
            return AgentStarterCatalogSnapshot.model_validate(
                raw_data
            )
        except ValidationError as exc:
            raise AgentStarterCatalogBankError(
                f"Invalid catalog snapshot: {path}"
            ) from exc
