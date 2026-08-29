from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from schemas.agent_starter import AgentStarterGoal


class AgentStarterQuestionKind(str, Enum):
    BOOLEAN = "boolean"


class AgentStarterQuestion(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    key: str = Field(min_length=1)
    goal: AgentStarterGoal
    prompt: str = Field(min_length=1)
    kind: AgentStarterQuestionKind
    reason: str = Field(min_length=1)


class AgentStarterQuestionSet(BaseModel):
    schema_version: Literal["0.1"] = "0.1"

    goal: AgentStarterGoal
    questions: list[AgentStarterQuestion] = Field(
        default_factory=list,
    )
