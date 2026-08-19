from observer.core.execution import ExecutionContext
from observer.providers.base import ProviderRequest
from observer.providers.mock import MockProvider, MockProviderConfig


def make_context() -> ExecutionContext:
    return ExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        prompt_id="test-001",
        provider="mock",
        model="mock-model",
    )


def test_mock_provider_returns_default_response():
    provider = MockProvider()

    result = provider.execute(
        context=make_context(),
        request=ProviderRequest(prompt="Test prompt"),
    )

    assert result.response_text == "Mock response"
    assert result.input_tokens == 10
    assert result.output_tokens == 20
    assert result.latency_ms == 100
    assert result.error_type is None


def test_mock_provider_uses_custom_configuration():
    provider = MockProvider(
        MockProviderConfig(
            response_text="Custom response",
            input_tokens=42,
            output_tokens=84,
            reasoning_tokens=12,
            latency_ms=250,
            time_to_first_token_ms=50,
            truncated=True,
        )
    )

    result = provider.execute(
        context=make_context(),
        request=ProviderRequest(prompt="Test prompt"),
    )

    assert result.response_text == "Custom response"
    assert result.input_tokens == 42
    assert result.output_tokens == 84
    assert result.reasoning_tokens == 12
    assert result.latency_ms == 250
    assert result.time_to_first_token_ms == 50
    assert result.truncated is True


def test_mock_provider_can_simulate_provider_error():
    provider = MockProvider(
        MockProviderConfig(
            error_type="rate_limit",
            latency_ms=500,
            retry_count=2,
        )
    )

    result = provider.execute(
        context=make_context(),
        request=ProviderRequest(prompt="Test prompt"),
    )

    assert result.error_type == "rate_limit"
    assert result.response_text == ""
    assert result.retry_count == 2


def test_mock_provider_tokens_per_second_uses_normalized_result():
    provider = MockProvider(
        MockProviderConfig(
            output_tokens=50,
            latency_ms=2000,
        )
    )

    result = provider.execute(
        context=make_context(),
        request=ProviderRequest(prompt="Test prompt"),
    )

    assert result.tokens_per_second == 25


def test_mock_provider_does_not_wait_for_configured_latency():
    provider = MockProvider(
        MockProviderConfig(
            latency_ms=60_000,
        )
    )

    result = provider.execute(
        context=make_context(),
        request=ProviderRequest(prompt="Test prompt"),
    )

    observed_delta_ms = (
        result.finished_at_utc - result.started_at_utc
    ).total_seconds() * 1000

    assert observed_delta_ms == 60_000
