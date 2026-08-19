import pytest

from observer.core.benchmark_runner import BenchmarkRunner
from observer.providers.mock import MockProvider, MockProviderConfig
from schemas.benchmark import (
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkPrompt,
)


def make_benchmark() -> BenchmarkPrompt:
    return BenchmarkPrompt(
        prompt_id="reasoning-001",
        benchmark_version="0.1",
        category=BenchmarkCategory.REASONING,
        difficulty=BenchmarkDifficulty.EASY,
        prompt="A farmer has 17 sheep. All but 9 run away. How many remain?",
        expected_characteristics=[
            "Returns 9 as the answer",
        ],
    )


def make_runner(
    provider: MockProvider | None = None,
) -> BenchmarkRunner:
    return BenchmarkRunner(
        provider=provider or MockProvider(),
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        model="mock-model",
    )


def test_benchmark_runner_executes_prompt():
    runner = make_runner()

    run = runner.run(make_benchmark())

    assert run.benchmark.prompt_id == "reasoning-001"
    assert run.observation.request.prompt.startswith("A farmer")
    assert run.observation.result.response_text == "Mock response"


def test_benchmark_runner_builds_execution_context():
    runner = make_runner()

    run = runner.run(make_benchmark())
    context = run.observation.context

    assert context.observer_id == "observer-test"
    assert context.region_code == "CL-Los-Lagos"
    assert context.benchmark_version == "0.1"
    assert context.prompt_id == "reasoning-001"
    assert context.provider == "mock"
    assert context.model == "mock-model"


def test_benchmark_runner_passes_generation_parameters():
    runner = make_runner()

    run = runner.run(
        make_benchmark(),
        temperature=0.25,
        max_tokens=512,
        metadata={"sample": 4},
    )

    request = run.observation.request

    assert request.temperature == 0.25
    assert request.max_tokens == 512
    assert request.metadata == {"sample": 4}


def test_benchmark_runner_preserves_metrics():
    provider = MockProvider(
        MockProviderConfig(
            input_tokens=100,
            output_tokens=50,
            latency_ms=1000,
            time_to_first_token_ms=200,
        )
    )

    runner = make_runner(provider)

    run = runner.run(make_benchmark())
    result = run.observation.result

    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.latency_ms == 1000
    assert result.time_to_first_token_ms == 200
    assert result.tokens_per_second == 50


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("observer_id", ""),
        ("region_code", ""),
        ("model", ""),
    ],
)
def test_benchmark_runner_rejects_empty_configuration(field, value):
    kwargs = {
        "provider": MockProvider(),
        "observer_id": "observer-test",
        "region_code": "CL-Los-Lagos",
        "model": "mock-model",
    }

    kwargs[field] = value

    with pytest.raises(ValueError):
        BenchmarkRunner(**kwargs)
