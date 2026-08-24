from __future__ import annotations

from observer.core.deterministic_task_evaluator import (
    DeterministicTaskEvaluator,
)
from observer.core.exact_output_task_evaluator import (
    ExactOutputTaskEvaluator,
)
from observer.core.json_structure_task_evaluator import (
    JsonStructureTaskEvaluator,
)
from observer.core.task_evaluator_registry import (
    TaskEvaluatorRegistry,
)


def build_default_task_evaluator_registry(
) -> TaskEvaluatorRegistry:
    registry = TaskEvaluatorRegistry()

    registry.register(
        "deterministic-evidence-v0-1",
        DeterministicTaskEvaluator(),
    )

    registry.register(
        "exact-output-v0-1",
        ExactOutputTaskEvaluator(),
    )

    registry.register(
        "json-structure-v0-1",
        JsonStructureTaskEvaluator(),
    )

    return registry
