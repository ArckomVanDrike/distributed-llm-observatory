from datetime import datetime, timezone

import pytest

from observer.core.execution import ExecutionContext, ExecutionResult
from observer.providers.base import ProviderAdapter, ProviderRequest


class DummyProvider(ProviderAdapter):
    provider_name = "dummy"

    def execute(
        self,
        context: ExecutionContext,
        request: ProviderRequest,
    ) -> ExecutionResult:
        now = datetime.now(timezone.utc)

        return ExecutionResult(
            context=context,
            started_at_utc=now,
            finished_at_utc=now,
            latency_ms=100,
            response_text=f"Echo: {request.prompt}",
            input_tokens=5,
            output_tokens=3,
        )


def make_context() -> ExecutionContext:
    return ExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        prompt_id="test-001",
        provider="dummy",
        model="dummy-model",
    )


def test_provider_request_defaults():
    request = ProviderRequest(prompt="Hello")

    assert request.prompt == "Hello"
    assert request.temperature is None
    assert request.max_tokens is None
    assert request.metadata is None


def test_dummy_provider_executes_request():
    provider = DummyProvider()

    result = provider.execute(
        context=make_context(),
        request=ProviderRequest(prompt="Hello"),
    )

    assert result.response_text == "Echo: Hello"
    assert result.output_tokens == 3
    assert result.context.provider == "dummy"


def test_provider_adapter_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        ProviderAdapter()
