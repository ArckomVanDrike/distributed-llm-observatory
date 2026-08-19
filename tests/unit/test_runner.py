import pytest

from observer.core.execution import ExecutionContext
from observer.core.runner import ObserverRunner
from observer.providers.base import ProviderRequest
from observer.providers.mock import MockProvider, MockProviderConfig


def make_context(
    provider: str = "mock",
) -> ExecutionContext:
    return ExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        prompt_id="reasoning-001",
        provider=provider,
        model="mock-model",
    )


def test_runner_executes_provider():
    runner = ObserverRunner(MockProvider())

    run = runner.run(
        context=make_context(),
        request=ProviderRequest(prompt="What is 2 + 2?"),
    )

    assert run.context.prompt_id == "reasoning-001"
    assert run.request.prompt == "What is 2 + 2?"
    assert run.result.response_text == "Mock response"
    assert run.result.error_type is None


def test_runner_preserves_execution_metrics():
    provider = MockProvider(
        MockProviderConfig(
            input_tokens=120,
            output_tokens=60,
            latency_ms=2000,
            time_to_first_token_ms=300,
        )
    )

    runner = ObserverRunner(provider)

    run = runner.run(
        context=make_context(),
        request=ProviderRequest(prompt="Benchmark prompt"),
    )

    assert run.result.input_tokens == 120
    assert run.result.output_tokens == 60
    assert run.result.latency_ms == 2000
    assert run.result.time_to_first_token_ms == 300
    assert run.result.tokens_per_second == 30


def test_runner_preserves_provider_errors():
    provider = MockProvider(
        MockProviderConfig(
            error_type="rate_limit",
            retry_count=3,
        )
    )

    runner = ObserverRunner(provider)

    run = runner.run(
        context=make_context(),
        request=ProviderRequest(prompt="Benchmark prompt"),
    )

    assert run.result.error_type == "rate_limit"
    assert run.result.retry_count == 3
    assert run.result.response_text == ""


def test_runner_rejects_provider_context_mismatch():
    runner = ObserverRunner(MockProvider())

    with pytest.raises(ValueError, match="does not match"):
        runner.run(
            context=make_context(provider="anthropic"),
            request=ProviderRequest(prompt="Benchmark prompt"),
        )
