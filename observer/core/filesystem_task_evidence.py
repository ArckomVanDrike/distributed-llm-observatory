from __future__ import annotations

from pathlib import Path

from observer.core.task_evidence import (
    TaskCriterionEvidence,
    TaskEvidenceCollector,
)


class FilesystemTaskEvidenceCollector(TaskEvidenceCollector):
    """
    Collects deterministic benchmark evidence from a filesystem workspace.

    This component observes post-execution state. It does not instruct or
    execute the SUT.
    """

    def __init__(
        self,
        *,
        workspace: Path,
        relative_path: str,
        expected_content: str,
    ) -> None:
        if not workspace.exists():
            raise ValueError(
                f"workspace does not exist: {workspace}"
            )

        if not workspace.is_dir():
            raise ValueError(
                f"workspace must be a directory: {workspace}"
            )

        requested_path = Path(relative_path)

        if requested_path.is_absolute():
            raise ValueError(
                "evidence path must be relative to the workspace."
            )

        self.workspace = workspace.resolve()
        self.relative_path = relative_path
        self.expected_content = expected_content

        target = (
            self.workspace
            / requested_path
        ).resolve()

        try:
            target.relative_to(self.workspace)
        except ValueError:
            raise ValueError(
                "evidence path escapes the workspace."
            ) from None

        self.target = target

    def collect(
        self,
    ) -> tuple[TaskCriterionEvidence, ...]:
        file_exists = self.target.is_file()

        contents_match = (
            file_exists
            and self.target.read_text(
                encoding="utf-8"
            )
            == self.expected_content
        )

        return (
            TaskCriterionEvidence(
                criterion_id="file-created",
                passed=file_exists,
                evidence=(
                    f"Observed file exists: "
                    f"{self.relative_path}"
                    if file_exists
                    else (
                        "Observed file is missing: "
                        f"{self.relative_path}"
                    )
                ),
            ),
            TaskCriterionEvidence(
                criterion_id="file-contents-match",
                passed=contents_match,
                evidence=(
                    "Observed file contents match "
                    "the expected content."
                    if contents_match
                    else (
                        "Observed file contents do not "
                        "match the expected content."
                        if file_exists
                        else (
                            "Content comparison was not "
                            "possible because the file "
                            "is missing."
                        )
                    )
                ),
            ),
        )
