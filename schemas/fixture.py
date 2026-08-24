from __future__ import annotations

from pathlib import PurePosixPath

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


class FixtureFile(BaseModel):
    path: str = Field(min_length=1)
    content: str

    @field_validator("path")
    @classmethod
    def validate_path(
        cls,
        value: str,
    ) -> str:
        if "\\" in value:
            raise ValueError(
                "fixture file path must use POSIX separators."
            )

        path = PurePosixPath(value)

        if path.is_absolute():
            raise ValueError(
                "fixture file path must be relative."
            )

        if value == "." or ".." in path.parts:
            raise ValueError(
                "fixture file path cannot escape the fixture root."
            )

        return value


class FilesystemFixture(BaseModel):
    schema_version: str = "0.1"

    fixture_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    files: list[FixtureFile] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_unique_paths(
        self,
    ) -> FilesystemFixture:
        paths = [
            fixture_file.path
            for fixture_file in self.files
        ]

        if len(paths) != len(set(paths)):
            raise ValueError(
                "fixture contains duplicate file paths."
            )

        return self
