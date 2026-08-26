from __future__ import annotations

from pathlib import Path
from uuid import UUID

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

        seen_session_ids = set()

        for artifact in artifacts:
            session_id = artifact.session.session_id

            if session_id in seen_session_ids:
                raise ValueError(
                    "Agent Lab run history contains "
                    f"duplicate session_id: {session_id}"
                )

            seen_session_ids.add(session_id)

        artifacts.sort(
            key=lambda artifact: (
                artifact.session.started_at_utc,
                str(artifact.session.session_id),
            )
        )

        return artifacts


    def get_by_session_id(
        self,
        session_id: UUID,
    ) -> AgentLabRunArtifact:
        for artifact in self.load_all():
            if artifact.session.session_id == session_id:
                return artifact

        raise ValueError(
            "Agent Lab run history does not contain "
            f"session_id: {session_id}"
        )


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
