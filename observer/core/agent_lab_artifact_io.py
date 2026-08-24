from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from schemas.agent_lab import AgentLabRunArtifact


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
