from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from observer.sut.base import (
    SUTAdapter,
    SUTExecutionContext,
    SUTExecutionResult,
    SUTRequest,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


@dataclass(frozen=True)
class LocalFilesystemWriteControl:
    path: str
    content: str


class LocalFilesystemSUTAdapter(SUTAdapter):
    """
    Reference local SUT constrained to an explicit filesystem workspace.
    """

    manifest = TargetManifest(
        target_id="local-filesystem-sut",
        display_name="Local Filesystem SUT",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.FILESYSTEM,
        },
    )

    def __init__(
        self,
        workspace: Path,
        *,
        control: LocalFilesystemWriteControl | None = None,
    ) -> None:
        if not workspace.exists():
            raise ValueError(
                f"workspace does not exist: {workspace}"
            )

        if not workspace.is_dir():
            raise ValueError(
                f"workspace must be a directory: {workspace}"
            )

        self.workspace = workspace.resolve()
        self.control = control

    def execute(
        self,
        context: SUTExecutionContext,
        request: SUTRequest,
    ) -> SUTExecutionResult:
        if self.control is None:
            raise ValueError(
                "Local filesystem reference SUT requires "
                "explicit control."
            )

        relative_path = self.control.path
        content = self.control.content

        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError(
                "write_file requires a non-empty path."
            )

        if not isinstance(content, str):
            raise ValueError(
                "write_file requires string content."
            )

        requested_path = Path(relative_path)

        if requested_path.is_absolute():
            raise ValueError(
                "write_file path must be relative to the workspace."
            )

        target = (
            self.workspace
            / requested_path
        ).resolve()

        try:
            target.relative_to(self.workspace)
        except ValueError:
            raise ValueError(
                "write_file path escapes the workspace."
            ) from None

        started = datetime.now(timezone.utc)

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        target.write_text(
            content,
            encoding="utf-8",
        )

        finished = datetime.now(timezone.utc)

        file_exists = target.is_file()
        contents_match = (
            file_exists
            and target.read_text(encoding="utf-8") == content
        )

        return SUTExecutionResult(
            context=context,
            started_at_utc=started,
            finished_at_utc=finished,
            latency_ms=(
                finished - started
            ).total_seconds()
            * 1000,
            task_completed=(
                file_exists
                and contents_match
            ),
        )
