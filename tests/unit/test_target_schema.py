import pytest
from pydantic import ValidationError

from observer.core.benchmark_compatibility import target_supports_benchmark
from schemas.benchmark import BenchmarkPrompt
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


def test_foundation_model_target_manifest():
    target = TargetManifest(
        target_id="openai-gpt",
        display_name="OpenAI GPT",
        target_type=TargetType.FOUNDATION_MODEL,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.VISION,
        },
    )

    assert target.schema_version == "0.1"
    assert target.target_id == "openai-gpt"
    assert target.target_type is TargetType.FOUNDATION_MODEL
    assert TargetCapability.TEXT in target.capabilities
    assert TargetCapability.VISION in target.capabilities


def test_agent_target_manifest():
    target = TargetManifest(
        target_id="coding-agent",
        display_name="Coding Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
            TargetCapability.CODE_EXECUTION,
            TargetCapability.FILESYSTEM,
        },
    )

    assert target.target_type is TargetType.AGENT
    assert TargetCapability.CODE_EXECUTION in target.capabilities


def test_ai_system_target_manifest():
    target = TargetManifest(
        target_id="custom-jarvis",
        display_name="Custom Jarvis",
        target_type=TargetType.AI_SYSTEM,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.VISION,
            TargetCapability.AUDIO_INPUT,
            TargetCapability.SPEECH_OUTPUT,
            TargetCapability.MEMORY,
            TargetCapability.BROWSER,
            TargetCapability.TOOLS,
        },
    )

    assert target.target_type is TargetType.AI_SYSTEM
    assert TargetCapability.MEMORY in target.capabilities


def test_target_requires_at_least_one_capability():
    with pytest.raises(ValidationError):
        TargetManifest(
            target_id="empty-target",
            display_name="Empty Target",
            target_type=TargetType.AI_SYSTEM,
            capabilities=set(),
        )


def test_target_id_uses_stable_slug_format():
    with pytest.raises(ValidationError):
        TargetManifest(
            target_id="Bad Target ID",
            display_name="Bad Target",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
            },
        )


def test_existing_benchmark_defaults_to_text_capability():
    benchmark = BenchmarkPrompt(
        prompt_id="reasoning-001",
        benchmark_version="0.1",
        category="reasoning",
        difficulty="medium",
        prompt="Test prompt.",
    )

    assert benchmark.required_capabilities == {
        TargetCapability.TEXT,
    }


def test_benchmark_can_require_multiple_capabilities():
    benchmark = BenchmarkPrompt(
        prompt_id="memory-001",
        benchmark_version="0.1",
        category="reasoning",
        difficulty="medium",
        prompt="Remember and recall a fact.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.MEMORY,
        },
    )

    assert benchmark.required_capabilities == {
        TargetCapability.TEXT,
        TargetCapability.MEMORY,
    }



def test_target_supports_compatible_benchmark():
    target = TargetManifest(
        target_id="vision-system",
        display_name="Vision System",
        target_type=TargetType.AI_SYSTEM,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.VISION,
        },
    )

    benchmark = BenchmarkPrompt(
        prompt_id="vision-001",
        benchmark_version="0.1",
        category="reasoning",
        difficulty="medium",
        prompt="Inspect the image.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.VISION,
        },
    )

    assert target_supports_benchmark(
        target,
        benchmark,
    ) is True


def test_target_rejects_benchmark_with_missing_capability():
    target = TargetManifest(
        target_id="text-only-model",
        display_name="Text Only Model",
        target_type=TargetType.FOUNDATION_MODEL,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    benchmark = BenchmarkPrompt(
        prompt_id="memory-001",
        benchmark_version="0.1",
        category="reasoning",
        difficulty="medium",
        prompt="Recall the stored fact.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.MEMORY,
        },
    )

    assert target_supports_benchmark(
        target,
        benchmark,
    ) is False
