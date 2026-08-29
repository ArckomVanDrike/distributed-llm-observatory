from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ExecutionPlatform(str, Enum):
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"


class ExecutionInterface(str, Enum):
    NATIVE = "native"
    BROWSER = "browser"
    UNKNOWN = "unknown"


class ExecutionAccessStatus(str, Enum):
    AVAILABLE = "available"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ExecutionEnvironment(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    platform: ExecutionPlatform
    interface: ExecutionInterface

    available_runtimes: list[str] | None = None

    accelerator_access: ExecutionAccessStatus = (
        ExecutionAccessStatus.UNKNOWN
    )
    filesystem_access: ExecutionAccessStatus = (
        ExecutionAccessStatus.UNKNOWN
    )

    limitations: list[str] = Field(
        default_factory=list,
    )

    @field_validator("available_runtimes")
    @classmethod
    def validate_available_runtimes(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None

        if any(not runtime.strip() for runtime in value):
            raise ValueError(
                "Runtime names must not be empty."
            )

        if len(value) != len(set(value)):
            raise ValueError(
                "Available runtime names must be unique."
            )

        return value
