from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from schemas.evaluation import TaskEvaluation
from schemas.target import TargetCapability, TargetManifest


class AgentTestSessionStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTestTaskSelectionStatus(str, Enum):
    SELECTED = "selected"
    INCOMPATIBLE = "incompatible"
    DISABLED = "disabled"


class AgentTestTaskSelection(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    task_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    benchmark_version: str = Field(min_length=1)

    status: AgentTestTaskSelectionStatus

    missing_capabilities: set[TargetCapability] = Field(
        default_factory=set,
    )
    family_mismatch: bool = False

    @model_validator(mode="after")
    def validate_selection(
        self,
    ) -> AgentTestTaskSelection:
        if self.status is AgentTestTaskSelectionStatus.INCOMPATIBLE:
            if (
                not self.missing_capabilities
                and not self.family_mismatch
            ):
                raise ValueError(
                    "An incompatible task selection must record "
                    "missing capabilities or a family mismatch."
                )

            return self

        if self.missing_capabilities:
            raise ValueError(
                "Only incompatible task selections may record "
                "missing capabilities."
            )

        if self.family_mismatch:
            raise ValueError(
                "Only incompatible task selections may record "
                "a family mismatch."
            )

        return self


class AgentTestTaskResult(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    task_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    benchmark_version: str = Field(min_length=1)

    started_at_utc: datetime
    finished_at_utc: datetime
    latency_ms: float = Field(ge=0)

    task_completed: bool
    output_text: str | None = None

    retry_count: int = Field(default=0, ge=0)
    human_intervention_count: int = Field(default=0, ge=0)
    error_type: str | None = None

    metrics: dict[str, Any] = Field(
        default_factory=dict,
    )

    evaluation: TaskEvaluation

    @model_validator(mode="after")
    def validate_task_result(
        self,
    ) -> AgentTestTaskResult:
        if (
            self.started_at_utc.tzinfo is None
            or self.finished_at_utc.tzinfo is None
        ):
            raise ValueError(
                "Task result timestamps must be timezone-aware."
            )

        if self.finished_at_utc < self.started_at_utc:
            raise ValueError(
                "finished_at_utc cannot precede started_at_utc."
            )

        if self.evaluation.task_id != self.task_id:
            raise ValueError(
                "evaluation task_id must match task_id."
            )

        return self


class AgentTestSession(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    session_id: UUID = Field(default_factory=uuid4)

    target: TargetManifest

    suite_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    suite_version: str = Field(min_length=1)

    status: AgentTestSessionStatus

    started_at_utc: datetime
    completed_at_utc: datetime | None = None

    selections: list[AgentTestTaskSelection] = Field(
        default_factory=list,
    )

    results: list[AgentTestTaskResult] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_session(
        self,
    ) -> AgentTestSession:
        if self.started_at_utc.tzinfo is None:
            raise ValueError(
                "started_at_utc must be timezone-aware."
            )

        if (
            self.completed_at_utc is not None
            and self.completed_at_utc.tzinfo is None
        ):
            raise ValueError(
                "completed_at_utc must be timezone-aware."
            )

        if self.status is AgentTestSessionStatus.RUNNING:
            if self.completed_at_utc is not None:
                raise ValueError(
                    "A running session cannot have "
                    "completed_at_utc."
                )

            return self

        if self.completed_at_utc is None:
            raise ValueError(
                "completed_at_utc is required for a "
                "completed or failed session."
            )

        if self.completed_at_utc < self.started_at_utc:
            raise ValueError(
                "completed_at_utc cannot precede "
                "started_at_utc."
            )

        return self


class AgentTechnicalReport(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    session_id: UUID

    target_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    suite_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    suite_version: str = Field(min_length=1)

    generated_at_utc: datetime

    total_tasks: int = Field(ge=0)
    passed_tasks: int = Field(ge=0)
    failed_tasks: int = Field(ge=0)

    task_completion_rate: float = Field(
        ge=0,
        le=1,
    )
    pass_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    median_latency_ms: float | None = Field(
        default=None,
        ge=0,
    )

    total_retries: int = Field(default=0, ge=0)
    total_human_interventions: int = Field(
        default=0,
        ge=0,
    )

    findings: list[str] = Field(
        default_factory=list,
    )
    recommendations: list[str] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_report(
        self,
    ) -> AgentTechnicalReport:
        if self.generated_at_utc.tzinfo is None:
            raise ValueError(
                "generated_at_utc must be timezone-aware."
            )

        if (
            self.passed_tasks + self.failed_tasks
            != self.total_tasks
        ):
            raise ValueError(
                "passed_tasks plus failed_tasks must equal "
                "total_tasks."
            )

        if self.total_tasks == 0:
            if self.pass_rate is not None:
                raise ValueError(
                    "pass_rate must be null when total_tasks "
                    "is zero."
                )

            return self

        expected_pass_rate = (
            self.passed_tasks / self.total_tasks
        )

        if (
            self.pass_rate is None
            or abs(
                self.pass_rate - expected_pass_rate
            ) > 1e-12
        ):
            raise ValueError(
                "pass_rate must match passed_tasks divided "
                "by total_tasks."
            )

        return self
