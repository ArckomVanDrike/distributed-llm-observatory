from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from pydantic import ValidationError

from schemas.agent_lab import AgentLabRunArtifact


class AgentLabArtifactIOError(Exception):
    """Raised when an Agent Lab run artifact cannot be loaded safely."""


def load_agent_lab_run_artifact(
    path: Path,
) -> AgentLabRunArtifact:
    try:
        raw_data = json.loads(
            path.read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise AgentLabArtifactIOError(
            f"Unable to read Agent Lab run artifact: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise AgentLabArtifactIOError(
            f"Invalid JSON in Agent Lab run artifact: {path}"
        ) from exc

    try:
        return AgentLabRunArtifact.model_validate(
            raw_data
        )
    except ValidationError as exc:
        raise AgentLabArtifactIOError(
            f"Invalid Agent Lab run artifact: {path}"
        ) from exc


def write_agent_lab_run_artifact(
    artifact: AgentLabRunArtifact,
    path: Path,
) -> None:
    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(
                artifact.model_dump_json(
                    indent=2,
                )
            )
            temporary_file.write("\n")

            temporary_path = Path(
                temporary_file.name
            )

        temporary_path.replace(path)

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()
