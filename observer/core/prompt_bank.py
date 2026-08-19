from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from schemas.benchmark import BenchmarkPrompt


class PromptBankError(Exception):
    """Raised when the benchmark prompt bank cannot be loaded safely."""


class PromptBank:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load_prompt(self, path: Path) -> BenchmarkPrompt:
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise PromptBankError(f"Unable to read prompt file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise PromptBankError(f"Invalid JSON in prompt file: {path}") from exc

        try:
            return BenchmarkPrompt.model_validate(raw_data)
        except ValidationError as exc:
            raise PromptBankError(f"Invalid benchmark prompt: {path}") from exc

    def load_all(self) -> list[BenchmarkPrompt]:
        if not self.root.exists():
            raise PromptBankError(
                f"Prompt bank directory does not exist: {self.root}"
            )

        prompts = [
            self.load_prompt(path)
            for path in sorted(self.root.rglob("*.json"))
        ]

        prompt_ids = [prompt.prompt_id for prompt in prompts]

        if len(prompt_ids) != len(set(prompt_ids)):
            raise PromptBankError("Duplicate prompt_id detected in prompt bank.")

        return prompts

    def load_enabled(self) -> list[BenchmarkPrompt]:
        return [
            prompt
            for prompt in self.load_all()
            if prompt.enabled
        ]
