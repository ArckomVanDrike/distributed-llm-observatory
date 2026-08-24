import pytest
from pydantic import ValidationError

from schemas.fixture import (
    FilesystemFixture,
    FixtureFile,
)


def test_filesystem_fixture_describes_initial_workspace():
    fixture = FilesystemFixture(
        fixture_id="filesystem-empty-v0-1",
        files=[],
    )

    assert fixture.schema_version == "0.1"
    assert fixture.fixture_id == "filesystem-empty-v0-1"
    assert fixture.files == []


def test_filesystem_fixture_can_define_text_files():
    fixture = FilesystemFixture(
        fixture_id="filesystem-seeded-v0-1",
        files=[
            FixtureFile(
                path="src/example.txt",
                content="initial content",
            ),
        ],
    )

    assert fixture.files[0].path == "src/example.txt"
    assert fixture.files[0].content == "initial content"


@pytest.mark.parametrize(
    "path",
    [
        "/tmp/escape.txt",
        "../escape.txt",
        "nested/../../escape.txt",
        "",
    ],
)
def test_fixture_file_rejects_unsafe_paths(path: str):
    with pytest.raises(ValidationError):
        FixtureFile(
            path=path,
            content="content",
        )


def test_filesystem_fixture_rejects_duplicate_paths():
    with pytest.raises(
        ValidationError,
        match="duplicate",
    ):
        FilesystemFixture(
            fixture_id="filesystem-duplicate-v0-1",
            files=[
                FixtureFile(
                    path="same.txt",
                    content="one",
                ),
                FixtureFile(
                    path="same.txt",
                    content="two",
                ),
            ],
        )
