from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DeviceClass(str, Enum):
    DESKTOP = "desktop"
    LAPTOP = "laptop"
    PHONE = "phone"
    TABLET = "tablet"
    UNKNOWN = "unknown"


class HardwareProfileSource(str, Enum):
    NATIVE = "native"
    BROWSER_LIMITED = "browser_limited"
    MANUAL = "manual"


class AcceleratorKind(str, Enum):
    GPU = "gpu"
    NPU = "npu"
    OTHER = "other"


class AcceleratorProfile(BaseModel):
    kind: AcceleratorKind
    name: str | None = Field(
        default=None,
        min_length=1,
    )
    memory_bytes: int | None = Field(
        default=None,
        gt=0,
    )


class HardwareProfile(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    device_class: DeviceClass
    source: HardwareProfileSource

    os_name: str | None = Field(
        default=None,
        min_length=1,
    )
    architecture: str | None = Field(
        default=None,
        min_length=1,
    )
    cpu_model: str | None = Field(
        default=None,
        min_length=1,
    )
    logical_cpu_count: int | None = Field(
        default=None,
        gt=0,
    )

    total_memory_bytes: int | None = Field(
        default=None,
        gt=0,
    )

    accelerators: list[AcceleratorProfile] = Field(
        default_factory=list,
    )
    limitations: list[str] = Field(
        default_factory=list,
    )
