from schemas.benchmark import BenchmarkPrompt
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
