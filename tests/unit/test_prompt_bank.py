import json
from pathlib import Path

import pytest

from observer.core.prompt_bank import PromptBank, PromptBankError
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
)


def write_prompt(path: Path, **overrides) -> None:
    data = {
        "prompt_id": "reasoning-001",
        "benchmark_version": "0.1",
        "category": "reasoning",
        "difficulty": "easy",
        "prompt": "Test prompt",
        "expected_characteristics": ["Be correct"],
        "scoring_method": "observatory_rubric_v0.1",
        "enabled": True,
    }

    data.update(overrides)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_prompt_bank_loads_valid_prompt(tmp_path):
    prompt_file = tmp_path / "reasoning-001.json"
    write_prompt(prompt_file)

    bank = PromptBank(tmp_path)
    prompts = bank.load_all()

    assert len(prompts) == 1
    assert prompts[0].prompt_id == "reasoning-001"
    assert prompts[0].category == BenchmarkCategory.REASONING
    assert prompts[0].difficulty == BenchmarkDifficulty.EASY


def test_prompt_bank_filters_disabled_prompts(tmp_path):
    write_prompt(
        tmp_path / "reasoning-001.json",
        enabled=False,
    )

    bank = PromptBank(tmp_path)

    assert bank.load_enabled() == []


def test_prompt_bank_rejects_invalid_json(tmp_path):
    prompt_file = tmp_path / "broken.json"
    prompt_file.write_text("{broken", encoding="utf-8")

    bank = PromptBank(tmp_path)

    with pytest.raises(PromptBankError, match="Invalid JSON"):
        bank.load_all()


def test_prompt_bank_rejects_invalid_schema(tmp_path):
    prompt_file = tmp_path / "invalid.json"
    write_prompt(prompt_file, difficulty="impossible")

    bank = PromptBank(tmp_path)

    with pytest.raises(PromptBankError, match="Invalid benchmark prompt"):
        bank.load_all()


def test_prompt_bank_rejects_duplicate_prompt_ids(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_prompt(first, prompt_id="duplicate-001")
    write_prompt(second, prompt_id="duplicate-001")

    bank = PromptBank(tmp_path)

    with pytest.raises(PromptBankError, match="Duplicate prompt_id"):
        bank.load_all()


def test_repository_prompt_bank_contains_valid_prompts():
    bank = PromptBank(Path("benchmark/prompts"))

    prompts = bank.load_enabled()

    assert prompts
    assert all(prompt.enabled for prompt in prompts)
