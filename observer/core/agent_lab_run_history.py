from __future__ import annotations

from pathlib import Path

from observer.core.agent_lab_artifact_io import (
    load_agent_lab_run_artifact,
)
from schemas.agent_lab import AgentLabRunArtifact


class AgentLabRunHistory:
    def __init__(
        self,
        root: Path,
    ) -> None:
        self.root = root

    def load_all(
        self,
    ) -> list[AgentLabRunArtifact]:
        artifacts = [
            load_agent_lab_run_artifact(path)
            for path in sorted(
                self.root.rglob("*.json")
            )
        ]

        artifacts.sort(
            key=lambda artifact: (
                artifact.session.started_at_utc,
                str(artifact.session.session_id),
            )
        )

        return artifacts


    def for_target(
        self,
        target_id: str,
    ) -> list[AgentLabRunArtifact]:
        return [
            artifact
            for artifact in self.load_all()
            if (
                artifact.session.target.target_id
                == target_id
            )
        ]
