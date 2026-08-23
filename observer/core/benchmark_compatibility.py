from schemas.benchmark import BenchmarkPrompt, BenchmarkTask
from schemas.target import TargetManifest


def target_supports_benchmark(
    target: TargetManifest,
    benchmark: BenchmarkPrompt,
) -> bool:
    if benchmark.family.value != target.target_type.value:
        return False

    return benchmark.required_capabilities.issubset(
        target.capabilities
    )



def target_supports_task(
    target: TargetManifest,
    task: BenchmarkTask,
) -> bool:
    if task.family.value != target.target_type.value:
        return False

    return task.required_capabilities.issubset(
        target.capabilities
    )
