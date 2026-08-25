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


class BenchmarkToolResult(BaseModel):
    tool_name: str = Field(min_length=1)

    result: dict[
        str,
        str | int | float | bool | None,
    ] = Field(default_factory=dict)


class BenchmarkToolFailure(BaseModel):
    tool_name: str = Field(min_length=1)
    status_code: int = Field(
        ge=400,
        le=599,
    )

    error: dict[
        str,
        str | int | float | bool | None,
    ] = Field(default_factory=dict)


class BenchmarkExpectedPropagation(BaseModel):
    source_action_index: int = Field(ge=0)
    source_result_field: str = Field(min_length=1)
    target_action_index: int = Field(ge=0)
    target_argument: str = Field(min_length=1)


class BenchmarkExpectedRecovery(BaseModel):
    failed_action_index: int = Field(ge=0)
    recovery_action_index: int = Field(ge=0)


class BenchmarkExpectedBranch(BaseModel):
    source_action_index: int = Field(ge=0)
    source_result_field: str = Field(min_length=1)
    expected_value: str | int | float | bool | None
    branch_action_index: int = Field(ge=0)


class BenchmarkExpectedActionCall(BaseModel):
    tool_name: str = Field(min_length=1)

    arguments: dict[
        str,
        str | int | float | bool | None,
    ] = Field(default_factory=dict)


class BenchmarkExpectedAction(
    BenchmarkExpectedActionCall
):
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

    tool_results: list[BenchmarkToolResult] = Field(
        default_factory=list,
    )

    tool_failures: list[BenchmarkToolFailure] = Field(
        default_factory=list,
    )

    expected_action: BenchmarkExpectedAction | None = None

    expected_actions: (
        list[BenchmarkExpectedActionCall] | None
    ) = Field(
        default=None,
        min_length=1,
    )

    expected_propagations: (
        list[BenchmarkExpectedPropagation] | None
    ) = Field(
        default=None,
        min_length=1,
    )

    expected_recovery: (
        BenchmarkExpectedRecovery | None
    ) = None

    expected_branch: (
        BenchmarkExpectedBranch | None
    ) = None

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
            and self.expected_actions is not None
        ):
            raise ValueError(
                "BenchmarkTask cannot define both "
                "expected_action and expected_actions."
            )

        has_expected_actions = (
            self.expected_action is not None
            or self.expected_actions is not None
        )

        if (
            has_expected_actions
            and TargetCapability.TOOLS
            not in self.required_capabilities
        ):
            raise ValueError(
                "BenchmarkTask with expected action data "
                "requires the tools capability."
            )

        return self

    @model_validator(mode="after")
    def validate_tool_failures_contract(
        self,
    ) -> BenchmarkTask:
        if not self.tool_failures:
            return self

        if (
            TargetCapability.TOOLS
            not in self.required_capabilities
        ):
            raise ValueError(
                "BenchmarkTask with tool_failures "
                "requires the tools capability."
            )

        if not self.available_tools:
            raise ValueError(
                "BenchmarkTask tool_failures "
                "requires available_tools."
            )

        available_tool_names = {
            tool.tool_name
            for tool in self.available_tools
        }

        failure_tool_names = [
            failure.tool_name
            for failure in self.tool_failures
        ]

        if (
            len(failure_tool_names)
            != len(set(failure_tool_names))
        ):
            raise ValueError(
                "BenchmarkTask tool_failures "
                "tool names must be unique."
            )

        unknown_tool_names = (
            set(failure_tool_names)
            - available_tool_names
        )

        if unknown_tool_names:
            raise ValueError(
                "BenchmarkTask tool_failures tool names "
                "must reference available_tools entries."
            )

        result_tool_names = {
            result.tool_name
            for result in self.tool_results
        }

        overlapping_tool_names = (
            set(failure_tool_names)
            & result_tool_names
        )

        if overlapping_tool_names:
            raise ValueError(
                "BenchmarkTask tool_results and "
                "tool_failures must reference "
                "different tools."
            )

        return self

    @model_validator(mode="after")
    def validate_tool_results_contract(
        self,
    ) -> BenchmarkTask:
        if not self.tool_results:
            return self

        if (
            TargetCapability.TOOLS
            not in self.required_capabilities
        ):
            raise ValueError(
                "BenchmarkTask with tool_results "
                "requires the tools capability."
            )

        if not self.available_tools:
            raise ValueError(
                "BenchmarkTask tool_results "
                "requires available_tools."
            )

        tool_names = {
            tool.tool_name
            for tool in self.available_tools
        }

        result_tool_names = [
            tool_result.tool_name
            for tool_result in self.tool_results
        ]

        if (
            len(result_tool_names)
            != len(set(result_tool_names))
        ):
            raise ValueError(
                "BenchmarkTask tool_results "
                "tool names must be unique."
            )

        unknown_tool_names = (
            set(result_tool_names)
            - tool_names
        )

        if unknown_tool_names:
            raise ValueError(
                "BenchmarkTask tool_results tool names "
                "must reference available_tools entries."
            )

        return self

    @model_validator(mode="after")
    def validate_expected_branch(
        self,
    ) -> BenchmarkTask:
        if self.expected_branch is None:
            return self

        if self.expected_actions is None:
            raise ValueError(
                "BenchmarkTask expected_branch "
                "requires expected_actions."
            )

        if not self.tool_results:
            raise ValueError(
                "BenchmarkTask expected_branch "
                "requires tool_results."
            )

        actions = self.expected_actions
        branch = self.expected_branch

        source_index = branch.source_action_index
        branch_index = branch.branch_action_index

        if (
            source_index >= len(actions)
            or branch_index >= len(actions)
        ):
            raise ValueError(
                "BenchmarkTask expected_branch "
                "action indices must reference "
                "expected_actions entries."
            )

        if source_index >= branch_index:
            raise ValueError(
                "BenchmarkTask expected_branch "
                "must flow from a source action "
                "to a later branch action."
            )

        source_action = actions[source_index]

        results_by_tool = {
            result.tool_name: result
            for result in self.tool_results
        }

        source_result = results_by_tool.get(
            source_action.tool_name
        )

        if (
            source_result is None
            or branch.source_result_field
            not in source_result.result
        ):
            raise ValueError(
                "BenchmarkTask expected_branch "
                "source_result_field must exist in "
                "the source tool result."
            )

        source_value = source_result.result[
            branch.source_result_field
        ]

        if source_value != branch.expected_value:
            raise ValueError(
                "BenchmarkTask expected_branch "
                "expected_value must match the "
                "configured source tool result."
            )

        return self

    @model_validator(mode="after")
    def validate_expected_recovery(
        self,
    ) -> BenchmarkTask:
        if self.expected_recovery is None:
            return self

        if self.expected_actions is None:
            raise ValueError(
                "BenchmarkTask expected_recovery "
                "requires expected_actions."
            )

        if not self.tool_failures:
            raise ValueError(
                "BenchmarkTask expected_recovery "
                "requires tool_failures."
            )

        actions = self.expected_actions
        recovery = self.expected_recovery

        failed_index = recovery.failed_action_index
        recovery_index = recovery.recovery_action_index

        if (
            failed_index >= len(actions)
            or recovery_index >= len(actions)
        ):
            raise ValueError(
                "BenchmarkTask expected_recovery "
                "action indices must reference "
                "expected_actions entries."
            )

        if failed_index >= recovery_index:
            raise ValueError(
                "BenchmarkTask expected_recovery "
                "must flow from a failed action "
                "to a later recovery action."
            )

        failed_action = actions[failed_index]

        failure_tool_names = {
            failure.tool_name
            for failure in self.tool_failures
        }

        if (
            failed_action.tool_name
            not in failure_tool_names
        ):
            raise ValueError(
                "BenchmarkTask expected_recovery "
                "failed action must reference a tool "
                "configured in tool_failures."
            )

        return self

    @model_validator(mode="after")
    def validate_expected_propagations(
        self,
    ) -> BenchmarkTask:
        if self.expected_propagations is None:
            return self

        if self.expected_actions is None:
            raise ValueError(
                "BenchmarkTask expected_propagations "
                "requires expected_actions."
            )

        if not self.tool_results:
            raise ValueError(
                "BenchmarkTask expected_propagations "
                "requires tool_results."
            )

        actions = self.expected_actions
        tool_results = {
            result.tool_name: result
            for result in self.tool_results
        }
        tool_contracts = {
            tool.tool_name: tool
            for tool in self.available_tools
        }

        for propagation in self.expected_propagations:
            source_index = propagation.source_action_index
            target_index = propagation.target_action_index

            if (
                source_index >= len(actions)
                or target_index >= len(actions)
            ):
                raise ValueError(
                    "BenchmarkTask expected_propagations "
                    "action indices must reference "
                    "expected_actions entries."
                )

            if source_index >= target_index:
                raise ValueError(
                    "BenchmarkTask expected_propagations "
                    "must flow from an earlier action "
                    "to a later action."
                )

            source_action = actions[source_index]
            target_action = actions[target_index]

            source_result = tool_results.get(
                source_action.tool_name
            )

            if (
                source_result is None
                or propagation.source_result_field
                not in source_result.result
            ):
                raise ValueError(
                    "BenchmarkTask expected_propagations "
                    "source_result_field must exist in "
                    "the source tool result."
                )

            target_contract = tool_contracts.get(
                target_action.tool_name
            )

            if (
                target_contract is None
                or propagation.target_argument
                not in target_contract.parameters
            ):
                raise ValueError(
                    "BenchmarkTask expected_propagations "
                    "target_argument must exist in "
                    "the target tool parameters."
                )

            if (
                propagation.target_argument
                in target_action.arguments
            ):
                raise ValueError(
                    "BenchmarkTask expected_propagations "
                    "target_argument cannot also be a "
                    "static expected action argument."
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

        if self.expected_actions is not None:
            if not self.available_tools:
                raise ValueError(
                    "BenchmarkTask expected_actions "
                    "requires available_tools."
                )

            unknown_tool_names = {
                action.tool_name
                for action in self.expected_actions
            } - set(tool_names)

            if unknown_tool_names:
                raise ValueError(
                    "BenchmarkTask expected_actions tool names "
                    "must reference available_tools entries."
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
