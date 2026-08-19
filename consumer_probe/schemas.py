from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


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
    observer_timezone: str | None = None

    platform: ConsumerPlatform
    account_tier: str | None = None
    model_label: str | None = None

    page_hostname: str | None = None
    measurement_mode: str = "consumer-ui-manual-v0.1"

    benchmark_version: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)

    input_mode: ProbeInputMode = ProbeInputMode.MANUAL

    scheduled_at_utc: datetime | None = None
    schedule_offset_ms: float | None = None

    started_at_utc: datetime
    first_output_at_utc: datetime | None = None
    completed_at_utc: datetime | None = None

    time_to_first_output_ms: float | None = Field(
        default=None,
        ge=0,
    )
    total_latency_ms: float | None = Field(
        default=None,
        ge=0,
    )

    response_text: str | None = None

    generation_failed: bool = False
    interrupted: bool = False
    retry_observed: bool = False

    response_capture_enabled: bool = False
    sharing_allowed: bool = False

    @model_validator(mode="after")
    def validate_schedule_provenance(
        self,
    ) -> ConsumerProbeRecord:
        if self.scheduled_at_utc is None:
            if self.schedule_offset_ms is not None:
                raise ValueError(
                    "schedule_offset_ms requires "
                    "scheduled_at_utc."
                )

            return self

        if self.schedule_offset_ms is None:
            raise ValueError(
                "schedule_offset_ms is required when "
                "scheduled_at_utc is present."
            )

        if (
            self.started_at_utc.tzinfo is None
            or self.scheduled_at_utc.tzinfo is None
        ):
            raise ValueError(
                "Schedule provenance timestamps must "
                "be timezone-aware."
            )

        expected_offset = (
            self.started_at_utc
            - self.scheduled_at_utc
        ).total_seconds() * 1000

        if abs(
            expected_offset
            - self.schedule_offset_ms
        ) > 1:
            raise ValueError(
                "schedule_offset_ms is inconsistent "
                "with scheduled and started timestamps."
            )

        return self


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
