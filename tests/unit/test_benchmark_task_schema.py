import pytest
from pydantic import ValidationError

from observer.core.benchmark_compatibility import target_supports_task
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkTask,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


def test_agent_benchmark_task():
    task = BenchmarkTask(
        task_id="agent-coding-001",
        benchmark_version="0.1",
        evaluator_id="test-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.CODING,
        difficulty=BenchmarkDifficulty.MEDIUM,
        task="Fix the failing tests in the provided repository.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.FILESYSTEM,
            TargetCapability.CODE_EXECUTION,
        },
        success_criteria=[
            "All existing tests pass.",
            "No unrelated files are modified.",
        ],
        fixture_id="repo-python-bug-001",
    )

    assert task.schema_version == "0.1"
    assert task.family is BenchmarkFamily.AGENT
    assert task.fixture_id == "repo-python-bug-001"
    assert len(task.success_criteria) == 2


def test_ai_system_benchmark_task():
    task = BenchmarkTask(
        task_id="memory-recall-001",
        benchmark_version="0.1",
        evaluator_id="test-evaluator-v0-1",
        family=BenchmarkFamily.AI_SYSTEM,
        category=BenchmarkCategory.REASONING,
        difficulty=BenchmarkDifficulty.MEDIUM,
        task="Recall a fact introduced earlier in the session.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.MEMORY,
        },
        success_criteria=[
            "The stored fact is recalled correctly.",
        ],
    )

    assert task.family is BenchmarkFamily.AI_SYSTEM
    assert task.fixture_id is None


def test_benchmark_task_rejects_foundation_model_family():
    with pytest.raises(
        ValidationError,
        match="BenchmarkTask",
    ):
        BenchmarkTask(
            task_id="reasoning-task-001",
            benchmark_version="0.1",
            evaluator_id="test-evaluator-v0-1",
            family=BenchmarkFamily.FOUNDATION_MODEL,
            category=BenchmarkCategory.REASONING,
            difficulty=BenchmarkDifficulty.MEDIUM,
            task="Solve the reasoning problem.",
            success_criteria=[
                "Correct answer.",
            ],
        )


def test_benchmark_task_requires_success_criteria():
    with pytest.raises(ValidationError):
        BenchmarkTask(
            task_id="agent-empty-001",
            benchmark_version="0.1",
            evaluator_id="test-evaluator-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.CODING,
            difficulty=BenchmarkDifficulty.MEDIUM,
            task="Perform the task.",
            success_criteria=[],
        )


def test_benchmark_task_id_uses_stable_slug_format():
    with pytest.raises(ValidationError):
        BenchmarkTask(
            task_id="Bad Task ID",
            benchmark_version="0.1",
            evaluator_id="test-evaluator-v0-1",
            family=BenchmarkFamily.AGENT,
            category=BenchmarkCategory.CODING,
            difficulty=BenchmarkDifficulty.MEDIUM,
            task="Perform the task.",
            success_criteria=[
                "Task succeeds.",
            ],
        )



def test_agent_target_supports_compatible_task():
    target = TargetManifest(
        target_id="coding-agent",
        display_name="Coding Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.FILESYSTEM,
            TargetCapability.CODE_EXECUTION,
        },
    )

    task = BenchmarkTask(
        task_id="agent-coding-001",
        benchmark_version="0.1",
        evaluator_id="test-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.CODING,
        difficulty=BenchmarkDifficulty.MEDIUM,
        task="Fix the failing tests.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.FILESYSTEM,
            TargetCapability.CODE_EXECUTION,
        },
        success_criteria=[
            "All tests pass.",
        ],
    )

    assert target_supports_task(target, task) is True


def test_agent_target_rejects_task_with_missing_capability():
    target = TargetManifest(
        target_id="text-agent",
        display_name="Text Agent",
        target_type=TargetType.AGENT,
        capabilities={
            TargetCapability.TEXT,
        },
    )

    task = BenchmarkTask(
        task_id="agent-coding-001",
        benchmark_version="0.1",
        evaluator_id="test-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.CODING,
        difficulty=BenchmarkDifficulty.MEDIUM,
        task="Fix the failing tests.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.CODE_EXECUTION,
        },
        success_criteria=[
            "All tests pass.",
        ],
    )

    assert target_supports_task(target, task) is False


def test_ai_system_rejects_agent_task_by_family():
    target = TargetManifest(
        target_id="custom-jarvis",
        display_name="Custom Jarvis",
        target_type=TargetType.AI_SYSTEM,
        capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
    )

    task = BenchmarkTask(
        task_id="agent-tool-001",
        benchmark_version="0.1",
        evaluator_id="test-evaluator-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.REASONING,
        difficulty=BenchmarkDifficulty.MEDIUM,
        task="Use a tool to complete the task.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.TOOLS,
        },
        success_criteria=[
            "Task completes successfully.",
        ],
    )

    assert target_supports_task(target, task) is False


def test_benchmark_task_declares_explicit_evaluator():
    task = BenchmarkTask(
        task_id="agent-eval-001",
        benchmark_version="0.1",
        evaluator_id="pytest-verifier-v0-1",
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.CODING,
        difficulty=BenchmarkDifficulty.MEDIUM,
        task="Run the repository test suite.",
        required_capabilities={
            TargetCapability.TEXT,
            TargetCapability.CODE_EXECUTION,
        },
        success_criteria=[
            "All tests pass.",
        ],
    )

    assert task.evaluator_id == "pytest-verifier-v0-1"
