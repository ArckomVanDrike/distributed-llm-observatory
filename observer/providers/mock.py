from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from observer.core.execution import ExecutionContext, ExecutionResult
from observer.providers.base import ProviderAdapter, ProviderRequest


@dataclass(frozen=True)
class MockProviderConfig:
    response_text: str = "Mock response"
    input_tokens: int = 10
    output_tokens: int = 20
    reasoning_tokens: int | None = None
    latency_ms: float = 100.0
    time_to_first_token_ms: float | None = 25.0
    retry_count: int = 0
    error_type: str | None = None
    truncated: bool = False


class MockProvider(ProviderAdapter):
    """
    Deterministic provider used for testing Observatory workflows.

    No external API calls are performed and no real latency is introduced.
    """

    provider_name = "mock"

    def __init__(self, config: MockProviderConfig | None = None) -> None:
        self.config = config or MockProviderConfig()

    def execute(
        self,
        context: ExecutionContext,
        request: ProviderRequest,
    ) -> ExecutionResult:
        from datetime import datetime, timezone

        started_at = datetime.now(timezone.utc)
        finished_at = started_at + timedelta(milliseconds=self.config.latency_ms)

        response_text = self.config.response_text

        if self.config.error_type is not None:
            response_text = ""

        return ExecutionResult(
            context=context,
            started_at_utc=started_at,
            finished_at_utc=finished_at,
            latency_ms=self.config.latency_ms,
            response_text=response_text,
            input_tokens=self.config.input_tokens,
            output_tokens=self.config.output_tokens,
            reasoning_tokens=self.config.reasoning_tokens,
            time_to_first_token_ms=self.config.time_to_first_token_ms,
            retry_count=self.config.retry_count,
            error_type=self.config.error_type,
            truncated=self.config.truncated,
        )
