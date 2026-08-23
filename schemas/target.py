from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TargetType(str, Enum):
    FOUNDATION_MODEL = "foundation_model"
    AGENT = "agent"
    AI_SYSTEM = "ai_system"


class TargetCapability(str, Enum):
    TEXT = "text"
    VISION = "vision"
    AUDIO_INPUT = "audio_input"
    SPEECH_OUTPUT = "speech_output"

    MEMORY = "memory"

    TOOLS = "tools"
    BROWSER = "browser"
    FILESYSTEM = "filesystem"
    CODE_EXECUTION = "code_execution"


class TargetManifest(BaseModel):
    schema_version: str = "0.1"

    target_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    display_name: str = Field(min_length=1)

    target_type: TargetType

    capabilities: set[TargetCapability] = Field(
        min_length=1,
    )
