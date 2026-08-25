from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from schemas.target import TargetCapability


class BenchmarkCategory(str, Enum):
    REASONING = "reasoning"
    CODING = "coding"
    MATHEMATICS = "mathematics"
    INSTRUCTION_FOLLOWING = "instruction_following"
    KNOWLEDGE = "knowledge"
    WRITING = "writing"
    TECHNICAL = "technical"


class BenchmarkDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BenchmarkFamily(str, Enum):
    FOUNDATION_MODEL = "foundation_model"
    AGENT = "agent"
    AI_SYSTEM = "ai_system"


class BenchmarkPrompt(BaseModel):
    prompt_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    benchmark_version: str = Field(min_length=1)
    category: BenchmarkCategory
    difficulty: BenchmarkDifficulty
    family: BenchmarkFamily = BenchmarkFamily.FOUNDATION_MODEL

    prompt: str = Field(min_length=1)
    expected_characteristics: list[str] = Field(default_factory=list)
    scoring_method: str = Field(
        default="observatory_rubric_v0.1",
        min_length=1,
    )

    required_capabilities: set[TargetCapability] = Field(
        default_factory=lambda: {
            TargetCapability.TEXT,
        },
        min_length=1,
    )

    enabled: bool = True


class BenchmarkSuccessCriterion(BaseModel):
    criterion_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str = Field(min_length=1)


class BenchmarkToolContract(BaseModel):
    tool_name: str = Field(min_length=1)
    description: str = Field(min_length=1)

    parameters: dict[
        str,
        Literal[
            "string",
            "integer",
            "number",
            "boolean",
            "null",
        ],
    ] = Field(default_factory=dict)


class BenchmarkExpectedAction(BaseModel):
    tool_name: str = Field(min_length=1)

    arguments: dict[
        str,
        str | int | float | bool | None,
    ] = Field(default_factory=dict)

    call_count: int = Field(
        default=1,
        ge=1,
    )


class BenchmarkTask(BaseModel):
    schema_version: str = "0.1"

    task_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    benchmark_version: str = Field(min_length=1)

    evaluator_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    family: BenchmarkFamily
    category: BenchmarkCategory
    difficulty: BenchmarkDifficulty

    task: str = Field(min_length=1)

    required_capabilities: set[TargetCapability] = Field(
        default_factory=lambda: {
            TargetCapability.TEXT,
        },
        min_length=1,
    )

    success_criteria: list[BenchmarkSuccessCriterion] = Field(
        min_length=1,
    )

    fixture_id: str | None = Field(
        default=None,
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    expected_output_text: str | None = Field(
        default=None,
        min_length=1,
    )

    expected_output_json_object: (
        dict[str, str | int | float | bool | None]
        | None
    ) = None

    available_tools: list[BenchmarkToolContract] = Field(
        default_factory=list,
    )

    expected_action: BenchmarkExpectedAction | None = None

    enabled: bool = True

    @model_validator(mode="after")
    def validate_task_family(
        self,
    ) -> BenchmarkTask:
        if self.family is BenchmarkFamily.FOUNDATION_MODEL:
            raise ValueError(
                "BenchmarkTask cannot use the "
                "foundation_model family."
            )

        return self

    @model_validator(mode="after")
    def validate_expected_action_capability(
        self,
    ) -> BenchmarkTask:
        if (
            self.expected_action is not None
            and TargetCapability.TOOLS
            not in self.required_capabilities
        ):
            raise ValueError(
                "BenchmarkTask with expected_action "
                "requires the tools capability."
            )

        return self

    @model_validator(mode="after")
    def validate_available_tools_contract(
        self,
    ) -> BenchmarkTask:
        if (
            self.available_tools
            and TargetCapability.TOOLS
            not in self.required_capabilities
        ):
            raise ValueError(
                "BenchmarkTask with available_tools "
                "requires the tools capability."
            )

        tool_names = [
            tool.tool_name
            for tool in self.available_tools
        ]

        if len(tool_names) != len(set(tool_names)):
            raise ValueError(
                "BenchmarkTask available_tools "
                "tool names must be unique."
            )

        if self.expected_action is not None:
            if not self.available_tools:
                raise ValueError(
                    "BenchmarkTask expected_action "
                    "requires available_tools."
                )

            if (
                self.expected_action.tool_name
                not in tool_names
            ):
                raise ValueError(
                    "BenchmarkTask expected_action tool_name "
                    "must reference an available_tools entry."
                )

        return self


class BenchmarkHarnessProfile(str, Enum):
    SHARED_WORKSPACE = "shared_workspace"
    SUT_PROTOCOL = "sut_protocol"


class BenchmarkSuite(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    suite_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    suite_version: str = Field(min_length=1)

    family: BenchmarkFamily
    harness_profile: BenchmarkHarnessProfile

    task_ids: list[str] = Field(
        min_length=1,
    )

    enabled: bool = True

    @field_validator("task_ids")
    @classmethod
    def validate_task_ids(
        cls,
        task_ids: list[str],
    ) -> list[str]:
        import re

        pattern = re.compile(
            r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
        )

        for task_id in task_ids:
            if not pattern.fullmatch(task_id):
                raise ValueError(
                    "BenchmarkSuite task_ids must use "
                    "stable slug format."
                )

        if len(task_ids) != len(set(task_ids)):
            raise ValueError(
                "BenchmarkSuite task_ids must be unique."
            )

        return task_ids

    @model_validator(mode="after")
    def validate_suite_family(
        self,
    ) -> BenchmarkSuite:
        if self.family is BenchmarkFamily.FOUNDATION_MODEL:
            raise ValueError(
                "BenchmarkSuite cannot use the "
                "foundation_model family."
            )

        return self
