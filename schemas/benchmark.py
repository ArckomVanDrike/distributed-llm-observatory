from __future__ import annotations

from enum import Enum

from pydantic import (
    BaseModel,
    Field,
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
    scoring_method: str = Field(default="observatory_rubric_v0.1", min_length=1)

    required_capabilities: set[TargetCapability] = Field(
        default_factory=lambda: {
            TargetCapability.TEXT,
        },
        min_length=1,
    )

    enabled: bool = True


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

    success_criteria: list[str] = Field(
        min_length=1,
    )

    fixture_id: str | None = Field(
        default=None,
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

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
