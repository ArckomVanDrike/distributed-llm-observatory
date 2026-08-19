from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from observer.core.execution import ExecutionContext, ExecutionResult


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] | None = None


class ProviderAdapter(ABC):
    """
    Base interface for all LLM provider adapters.

    Concrete implementations must translate Observatory requests into
    provider-specific API calls and return a normalized ExecutionResult.
    """

    provider_name: str

    @abstractmethod
    def execute(
        self,
        context: ExecutionContext,
        request: ProviderRequest,
    ) -> ExecutionResult:
        """
        Execute a benchmark request against the provider.

        Implementations are responsible for:
        - measuring latency,
        - collecting token usage when available,
        - capturing errors in normalized form,
        - returning a provider-independent ExecutionResult.
        """
        raise NotImplementedError
