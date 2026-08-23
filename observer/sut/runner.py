from __future__ import annotations

from dataclasses import dataclass

from observer.sut.base import (
    SUTAdapter,
    SUTExecutionContext,
    SUTExecutionResult,
    SUTRequest,
)


@dataclass(frozen=True)
class SUTRun:
    context: SUTExecutionContext
    request: SUTRequest
    result: SUTExecutionResult


class SUTRunner:
    """
    Coordinates execution of an end-to-end task through a SUT adapter.
    """

    def __init__(
        self,
        adapter: SUTAdapter,
    ) -> None:
        self.adapter = adapter

    def run(
        self,
        context: SUTExecutionContext,
        request: SUTRequest,
    ) -> SUTRun:
        if (
            context.target_id
            != self.adapter.manifest.target_id
        ):
            raise ValueError(
                "Execution context target does not match "
                "the selected SUT adapter: "
                f"context={context.target_id!r}, "
                f"adapter={self.adapter.manifest.target_id!r}."
            )

        result = self.adapter.execute(
            context=context,
            request=request,
        )

        if result.context != context:
            raise ValueError(
                "SUT adapter returned an execution result "
                "with a different context."
            )

        return SUTRun(
            context=context,
            request=request,
            result=result,
        )
