from observer.core.default_task_evaluator_registry import (
    build_default_task_evaluator_registry,
)
from observer.core.deterministic_task_evaluator import (
    DeterministicTaskEvaluator,
)
from observer.core.exact_output_task_evaluator import (
    ExactOutputTaskEvaluator,
)
from observer.core.json_structure_task_evaluator import (
    JsonStructureTaskEvaluator,
)
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkFamily,
    BenchmarkSuccessCriterion,
    BenchmarkTask,
)
from schemas.target import TargetCapability


def build_task(
    *,
    evaluator_id: str,
) -> BenchmarkTask:
    return BenchmarkTask(
        schema_version="0.1",
        task_id="agent-registry-test-001",
        benchmark_version="0.1",
        evaluator_id=evaluator_id,
        family=BenchmarkFamily.AGENT,
        category=BenchmarkCategory.TECHNICAL,
        difficulty=BenchmarkDifficulty.EASY,
        task="Complete the task.",
        required_capabilities={
            TargetCapability.TEXT,
        },
        success_criteria=[
            BenchmarkSuccessCriterion(
                criterion_id="completed",
                description="The task is complete.",
            ),
        ],
    )


def test_default_registry_registers_deterministic_evidence_evaluator():
    registry = build_default_task_evaluator_registry()

    evaluator = registry.resolve(
        build_task(
            evaluator_id="deterministic-evidence-v0-1",
        )
    )

    assert isinstance(
        evaluator,
        DeterministicTaskEvaluator,
    )


def test_default_registry_registers_exact_output_evaluator():
    registry = build_default_task_evaluator_registry()

    evaluator = registry.resolve(
        build_task(
            evaluator_id="exact-output-v0-1",
        )
    )

    assert isinstance(
        evaluator,
        ExactOutputTaskEvaluator,
    )



def test_default_registry_registers_json_structure_evaluator():
    registry = build_default_task_evaluator_registry()

    evaluator = registry.resolve(
        build_task(
            evaluator_id="json-structure-v0-1",
        )
    )

    assert isinstance(
        evaluator,
        JsonStructureTaskEvaluator,
    )
