from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ConsumerPlatform(str, Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OTHER = "other"


class ProbeInputMode(str, Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"


class ConsumerProbeRecord(BaseModel):
    schema_version: str = "0.1"
    probe_id: UUID = Field(default_factory=uuid4)

    observer_id: str = Field(min_length=1)
    region_code: str = Field(min_length=2)

    platform: ConsumerPlatform
    account_tier: str | None = None
    model_label: str | None = None

    benchmark_version: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)

    input_mode: ProbeInputMode = ProbeInputMode.MANUAL

    started_at_utc: datetime
    first_output_at_utc: datetime | None = None
    completed_at_utc: datetime | None = None

    time_to_first_output_ms: float | None = Field(default=None, ge=0)
    total_latency_ms: float | None = Field(default=None, ge=0)

    response_text: str | None = None

    generation_failed: bool = False
    interrupted: bool = False
    retry_observed: bool = False

    response_capture_enabled: bool = False
    sharing_allowed: bool = False


class ConsumerProbeEnvelope(BaseModel):
    record: ConsumerProbeRecord

    def shareable_record(self) -> dict:
        """
        Return the representation that may leave the local machine.

        Response text is removed unless both local capture and sharing
        have explicitly been enabled.
        """
        data = self.record.model_dump(mode="json")

        if not (
            self.record.response_capture_enabled
            and self.record.sharing_allowed
        ):
            data["response_text"] = None

        return data
