from schemas.benchmark import BenchmarkPrompt
from schemas.target import TargetManifest


def target_supports_benchmark(
    target: TargetManifest,
    benchmark: BenchmarkPrompt,
) -> bool:
    return benchmark.required_capabilities.issubset(
        target.capabilities
    )
