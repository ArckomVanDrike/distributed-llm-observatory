from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ObserverConfigError(Exception):
    """Raised when local Observer configuration is invalid."""


@dataclass(frozen=True)
class ObserverConfig:
    observer_id: str
    region_code: str
    storage_path: Path
    observer_version: str = "0.1"

    @classmethod
    def from_environment(cls) -> ObserverConfig:
        observer_id = os.getenv("OBSERVATORY_ID", "").strip()
        region_code = os.getenv("OBSERVATORY_REGION", "").strip()
        storage_path = Path(
            os.getenv(
                "OBSERVATORY_STORAGE",
                "data/observatory.db",
            )
        )

        if not observer_id:
            raise ObserverConfigError(
                "OBSERVATORY_ID is required."
            )

        if not region_code:
            raise ObserverConfigError(
                "OBSERVATORY_REGION is required."
            )

        return cls(
            observer_id=observer_id,
            region_code=region_code,
            storage_path=storage_path,
        )
