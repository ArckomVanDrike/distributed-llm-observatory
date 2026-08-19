from __future__ import annotations

from dataclasses import dataclass

from observer.core.execution import ExecutionContext, ExecutionResult
from observer.providers.base import ProviderAdapter, ProviderRequest


@dataclass(frozen=True)
class ObserverRun:
    context: ExecutionContext
    request: ProviderRequest
    result: ExecutionResult


class ObserverRunner:
    """
    Coordinates execution of a benchmark prompt through a provider adapter.

    The runner is provider-agnostic. It verifies that the execution context
    matches the selected provider and returns a normalized ObserverRun.
    """

    def __init__(self, provider: ProviderAdapter) -> None:
        self.provider = provider

    def run(
        self,
        context: ExecutionContext,
        request: ProviderRequest,
    ) -> ObserverRun:
        if context.provider != self.provider.provider_name:
            raise ValueError(
                "Execution context provider does not match the selected "
                f"adapter: context={context.provider!r}, "
                f"adapter={self.provider.provider_name!r}."
            )

        result = self.provider.execute(
            context=context,
            request=request,
        )

        if result.context != context:
            raise ValueError(
                "Provider returned an execution result with a different context."
            )

        return ObserverRun(
            context=context,
            request=request,
            result=result,
        )
