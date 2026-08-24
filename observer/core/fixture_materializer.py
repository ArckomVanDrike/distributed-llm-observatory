from __future__ import annotations

from pathlib import Path

from schemas.fixture import FilesystemFixture


def materialize_filesystem_fixture(
    fixture: FilesystemFixture,
    root: Path,
) -> None:
    if not root.exists():
        raise ValueError(
            f"fixture root does not exist: {root}"
        )

    if not root.is_dir():
        raise ValueError(
            f"fixture root must be a directory: {root}"
        )

    resolved_root = root.resolve()

    for fixture_file in fixture.files:
        target = (
            resolved_root
            / fixture_file.path
        ).resolve()

        try:
            target.relative_to(
                resolved_root
            )
        except ValueError:
            raise ValueError(
                "fixture file path escapes "
                "the fixture root."
            ) from None

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            fixture_file.content,
            encoding="utf-8",
        )
