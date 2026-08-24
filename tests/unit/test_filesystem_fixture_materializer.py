from pathlib import Path

import pytest

from observer.core.fixture_materializer import (
    materialize_filesystem_fixture,
)
from schemas.fixture import (
    FilesystemFixture,
    FixtureFile,
)


def test_materializer_creates_declared_files(
    tmp_path: Path,
):
    fixture = FilesystemFixture(
        fixture_id="filesystem-seeded-v0-1",
        files=[
            FixtureFile(
                path="src/input.txt",
                content="hello",
            ),
        ],
    )

    materialize_filesystem_fixture(
        fixture,
        tmp_path,
    )

    assert (
        tmp_path / "src/input.txt"
    ).read_text(encoding="utf-8") == "hello"


def test_materializer_preserves_exact_contents(
    tmp_path: Path,
):
    fixture = FilesystemFixture(
        fixture_id="filesystem-exact-v0-1",
        files=[
            FixtureFile(
                path="probe.txt",
                content="line one\nline two\n",
            ),
        ],
    )

    materialize_filesystem_fixture(
        fixture,
        tmp_path,
    )

    assert (
        tmp_path / "probe.txt"
    ).read_bytes() == b"line one\nline two\n"


def test_materializer_requires_existing_directory(
    tmp_path: Path,
):
    missing = tmp_path / "missing"

    fixture = FilesystemFixture(
        fixture_id="filesystem-empty-v0-1",
        files=[],
    )

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        materialize_filesystem_fixture(
            fixture,
            missing,
        )


def test_materializer_rejects_non_directory_root(
    tmp_path: Path,
):
    path = tmp_path / "file"
    path.write_text(
        "x",
        encoding="utf-8",
    )

    fixture = FilesystemFixture(
        fixture_id="filesystem-empty-v0-1",
        files=[],
    )

    with pytest.raises(
        ValueError,
        match="must be a directory",
    ):
        materialize_filesystem_fixture(
            fixture,
            path,
        )
