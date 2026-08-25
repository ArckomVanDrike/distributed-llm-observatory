from __future__ import annotations

from datetime import datetime
from enum import Enum
from statistics import median
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

    observer_id: str | None = Field(
        default=None,
        min_length=1,
    )
    region_code: str | None = Field(
        default=None,
        min_length=1,
    )

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
        result_task_ids = [
            result.task_id
            for result in self.results
        ]

        if len(result_task_ids) != len(
            set(result_task_ids)
        ):
            raise ValueError(
                "Session results must contain unique "
                "task_id values."
            )

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


class AgentLabRunArtifact(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    session: AgentTestSession
    technical_report: AgentTechnicalReport

    @model_validator(mode="after")
    def validate_artifact(
        self,
    ) -> AgentLabRunArtifact:
        if (
            self.technical_report.session_id
            != self.session.session_id
        ):
            raise ValueError(
                "technical_report session_id must match "
                "session session_id."
            )

        if (
            self.technical_report.target_id
            != self.session.target.target_id
        ):
            raise ValueError(
                "technical_report target_id must match "
                "session target_id."
            )

        if (
            self.technical_report.suite_id
            != self.session.suite_id
        ):
            raise ValueError(
                "technical_report suite_id must match "
                "session suite_id."
            )

        if (
            self.technical_report.suite_version
            != self.session.suite_version
        ):
            raise ValueError(
                "technical_report suite_version must match "
                "session suite_version."
            )

        results = self.session.results
        total_tasks = len(results)

        passed_tasks = sum(
            1
            for result in results
            if result.evaluation.passed
        )
        failed_tasks = total_tasks - passed_tasks

        completed_tasks = sum(
            1
            for result in results
            if result.task_completed
        )

        expected_summary = {
            "total_tasks": total_tasks,
            "passed_tasks": passed_tasks,
            "failed_tasks": failed_tasks,
            "task_completion_rate": (
                completed_tasks / total_tasks
                if total_tasks
                else 0.0
            ),
            "pass_rate": (
                passed_tasks / total_tasks
                if total_tasks
                else None
            ),
            "median_latency_ms": (
                float(
                    median(
                        result.latency_ms
                        for result in results
                    )
                )
                if results
                else None
            ),
            "total_retries": sum(
                result.retry_count
                for result in results
            ),
            "total_human_interventions": sum(
                result.human_intervention_count
                for result in results
            ),
        }

        actual_summary = {
            "total_tasks": (
                self.technical_report.total_tasks
            ),
            "passed_tasks": (
                self.technical_report.passed_tasks
            ),
            "failed_tasks": (
                self.technical_report.failed_tasks
            ),
            "task_completion_rate": (
                self.technical_report.task_completion_rate
            ),
            "pass_rate": (
                self.technical_report.pass_rate
            ),
            "median_latency_ms": (
                self.technical_report.median_latency_ms
            ),
            "total_retries": (
                self.technical_report.total_retries
            ),
            "total_human_interventions": (
                self.technical_report
                .total_human_interventions
            ),
        }

        if actual_summary != expected_summary:
            raise ValueError(
                "technical_report summary must match "
                "session results."
            )

        return self
