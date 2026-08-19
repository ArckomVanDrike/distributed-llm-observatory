from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, ValidationError, model_validator

from consumer_probe.schemas import (
    ConsumerPlatform,
    ConsumerProbeRecord,
    ProbeInputMode,
)


class ConsumerProbeImportError(Exception):
    """Raised when a Consumer Probe export cannot be imported safely."""


class BrowserProbeRecord(BaseModel):
    schema_version: str
    probe_id: UUID

    prompt_id: str = Field(min_length=1)
    benchmark_version: str = Field(min_length=1)

    scheduled_at_utc: datetime | None = None
    schedule_offset_ms: float | None = None

    platform: ConsumerPlatform
    page_hostname: str = Field(min_length=1)

    started_at_ms: int = Field(ge=0)
    started_at_utc: datetime

    first_output_at_ms: int | None = Field(default=None, ge=0)
    first_output_at_utc: datetime | None = None

    completed_at_ms: int = Field(ge=0)
    completed_at_utc: datetime

    time_to_first_output_ms: float | None = Field(
        default=None,
        ge=0,
    )
    total_latency_ms: float = Field(ge=0)

    generation_failed: bool = False
    interrupted: bool = False
    retry_observed: bool = False

    response_capture_enabled: bool = False
    response_text: str | None = None

    measurement_mode: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_temporal_consistency(self) -> BrowserProbeRecord:
        if self.scheduled_at_utc is None:
            if self.schedule_offset_ms is not None:
                raise ValueError(
                    "schedule_offset_ms requires "
                    "scheduled_at_utc."
                )
        else:
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

        expected_total = self.completed_at_ms - self.started_at_ms

        if expected_total < 0:
            raise ValueError(
                "completed_at_ms cannot precede started_at_ms."
            )

        if abs(expected_total - self.total_latency_ms) > 1:
            raise ValueError(
                "total_latency_ms is inconsistent with timestamps."
            )

        if self.first_output_at_ms is None:
            if self.first_output_at_utc is not None:
                raise ValueError(
                    "first_output_at_utc must be null when "
                    "first_output_at_ms is null."
                )

            if self.time_to_first_output_ms is not None:
                raise ValueError(
                    "time_to_first_output_ms must be null when "
                    "first output was not recorded."
                )
        else:
            if self.first_output_at_ms < self.started_at_ms:
                raise ValueError(
                    "first output cannot precede probe start."
                )

            if self.first_output_at_ms > self.completed_at_ms:
                raise ValueError(
                    "first output cannot occur after completion."
                )

            expected_ttfo = (
                self.first_output_at_ms - self.started_at_ms
            )

            if self.time_to_first_output_ms is None:
                raise ValueError(
                    "time_to_first_output_ms is required when "
                    "first output is recorded."
                )

            if (
                abs(
                    expected_ttfo
                    - self.time_to_first_output_ms
                )
                > 1
            ):
                raise ValueError(
                    "time_to_first_output_ms is inconsistent "
                    "with timestamps."
                )

        if (
            not self.response_capture_enabled
            and self.response_text is not None
        ):
            raise ValueError(
                "response_text cannot be present when response "
                "capture is disabled."
            )

        return self


class ConsumerProbeExport(BaseModel):
    export_schema_version: str
    exported_at_utc: datetime
    sample_count: int = Field(ge=0)
    records: list[BrowserProbeRecord]

    @model_validator(mode="after")
    def validate_export(self) -> ConsumerProbeExport:
        if self.sample_count != len(self.records):
            raise ValueError(
                "sample_count does not match number of records."
            )

        probe_ids = [
            record.probe_id
            for record in self.records
        ]

        if len(probe_ids) != len(set(probe_ids)):
            raise ValueError(
                "Duplicate probe_id detected in export."
            )

        return self


def load_export(path: Path) -> ConsumerProbeExport:
    try:
        raw_data = json.loads(
            path.read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise ConsumerProbeImportError(
            f"Unable to read Consumer Probe export: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ConsumerProbeImportError(
            f"Invalid JSON in Consumer Probe export: {path}"
        ) from exc

    try:
        return ConsumerProbeExport.model_validate(raw_data)
    except ValidationError as exc:
        raise ConsumerProbeImportError(
            f"Invalid Consumer Probe export: {path}"
        ) from exc


def normalize_export(
    export: ConsumerProbeExport,
    *,
    observer_id: str,
    region_code: str,
    observer_timezone: str | None = None,
) -> list[ConsumerProbeRecord]:
    if not observer_id.strip():
        raise ConsumerProbeImportError(
            "observer_id cannot be empty."
        )

    if not region_code.strip():
        raise ConsumerProbeImportError(
            "region_code cannot be empty."
        )

    if observer_timezone is not None:
        try:
            ZoneInfo(observer_timezone)
        except ZoneInfoNotFoundError as exc:
            raise ConsumerProbeImportError(
                f"Invalid observer timezone: {observer_timezone}"
            ) from exc

    return [
        ConsumerProbeRecord(
            schema_version=record.schema_version,
            probe_id=record.probe_id,
            observer_id=observer_id,
            region_code=region_code,
            observer_timezone=observer_timezone,
            platform=record.platform,
            page_hostname=record.page_hostname,
            measurement_mode=record.measurement_mode,
            benchmark_version=record.benchmark_version,
            prompt_id=record.prompt_id,
            input_mode=ProbeInputMode.MANUAL,
            scheduled_at_utc=record.scheduled_at_utc,
            schedule_offset_ms=record.schedule_offset_ms,
            started_at_utc=record.started_at_utc,
            first_output_at_utc=record.first_output_at_utc,
            completed_at_utc=record.completed_at_utc,
            time_to_first_output_ms=(
                record.time_to_first_output_ms
            ),
            total_latency_ms=record.total_latency_ms,
            response_text=record.response_text,
            generation_failed=record.generation_failed,
            interrupted=record.interrupted,
            retry_observed=record.retry_observed,
            response_capture_enabled=(
                record.response_capture_enabled
            ),
            sharing_allowed=False,
        )
        for record in export.records
    ]


def import_export(
    path: Path,
    *,
    observer_id: str,
    region_code: str,
    observer_timezone: str | None = None,
) -> list[ConsumerProbeRecord]:
    export = load_export(path)

    return normalize_export(
        export,
        observer_id=observer_id,
        region_code=region_code,
        observer_timezone=observer_timezone,
    )
