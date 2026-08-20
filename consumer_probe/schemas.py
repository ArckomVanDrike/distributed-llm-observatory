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


class LocalTelemetryRecord(BaseModel):
    telemetry_schema_version: str = "0.2"
    probe_id: UUID

    started_at_utc: datetime
    stopped_at_utc: datetime

    sample_count: int = Field(ge=0)
    duration_ms: float = Field(ge=0)

    collector_version: str | None = None
    browser_scope: str | None = None
    memory_method: str | None = None

    fast_interval_target_ms: float | None = Field(
        default=None,
        gt=0,
    )
    pss_interval_target_ms: float | None = Field(
        default=None,
        gt=0,
    )

    peak_browser_process_count: int | None = Field(
        default=None,
        ge=0,
    )
    peak_browser_rss_bytes: int | None = Field(
        default=None,
        ge=0,
    )
    peak_browser_pss_bytes: int | None = Field(
        default=None,
        ge=0,
    )
    pss_sample_count: int | None = Field(
        default=None,
        ge=0,
    )
    peak_browser_cpu_percent: float | None = Field(
        default=None,
        ge=0,
    )

    min_system_memory_available_bytes: int | None = Field(
        default=None,
        ge=0,
    )
    peak_system_cpu_percent: float | None = Field(
        default=None,
        ge=0,
    )

    @model_validator(mode="after")
    def validate_local_telemetry(
        self,
    ) -> LocalTelemetryRecord:
        if (
            self.started_at_utc.tzinfo is None
            or self.stopped_at_utc.tzinfo is None
        ):
            raise ValueError(
                "Local telemetry timestamps must "
                "be timezone-aware."
            )

        if (
            self.stopped_at_utc
            < self.started_at_utc
        ):
            raise ValueError(
                "Local telemetry stop cannot "
                "precede start."
            )

        provenance_values = (
            self.collector_version,
            self.browser_scope,
            self.memory_method,
            self.fast_interval_target_ms,
        )

        if (
            self.telemetry_schema_version == "0.2"
            and not all(
                value is not None
                for value in provenance_values
            )
        ):
            raise ValueError(
                "Telemetry schema 0.2 requires "
                "complete collector provenance."
            )

        if any(
            value is not None
            for value in provenance_values
        ) and not all(
            value is not None
            for value in provenance_values
        ):
            raise ValueError(
                "Local telemetry provenance must "
                "be complete when present."
            )

        if (
            self.pss_interval_target_ms is not None
            and self.fast_interval_target_ms is None
        ):
            raise ValueError(
                "pss_interval_target_ms requires "
                "fast_interval_target_ms."
            )

        if (
            self.pss_interval_target_ms is not None
            and self.fast_interval_target_ms is not None
            and self.pss_interval_target_ms
            < self.fast_interval_target_ms
        ):
            raise ValueError(
                "pss_interval_target_ms cannot be "
                "shorter than fast_interval_target_ms."
            )

        if (
            self.pss_sample_count is not None
            and self.pss_sample_count > self.sample_count
        ):
            raise ValueError(
                "pss_sample_count cannot exceed "
                "sample_count."
            )

        if (
            self.pss_sample_count is not None
            and self.pss_sample_count > 0
            and self.peak_browser_pss_bytes is None
        ):
            raise ValueError(
                "Positive pss_sample_count requires "
                "peak_browser_pss_bytes."
            )

        if (
            self.pss_sample_count == 0
            and self.peak_browser_pss_bytes is not None
        ):
            raise ValueError(
                "pss_sample_count cannot be zero when "
                "peak_browser_pss_bytes is present."
            )

        return self


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

    local_telemetry: LocalTelemetryRecord | None = None
    local_telemetry_error: str | None = None

    @model_validator(mode="after")
    def validate_schedule_provenance(
        self,
    ) -> ConsumerProbeRecord:
        if (
            self.local_telemetry is not None
            and self.local_telemetry.probe_id
            != self.probe_id
        ):
            raise ValueError(
                "local_telemetry probe_id must match "
                "Consumer Probe probe_id."
            )

        if (
            self.local_telemetry is not None
            and self.local_telemetry_error is not None
        ):
            raise ValueError(
                "local_telemetry and "
                "local_telemetry_error cannot both "
                "be present."
            )

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
