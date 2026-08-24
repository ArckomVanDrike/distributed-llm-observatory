from __future__ import annotations

import json
from urllib.parse import urlparse
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)

from observer.sut.base import (
    SUTAdapter,
    SUTExecutionContext,
    SUTExecutionResult,
    SUTRequest,
)
from schemas.sut_protocol import (
    SUTProtocolExecutionContext,
    SUTProtocolExecutionRequest,
    SUTProtocolExecutionResponse,
    SUTProtocolManifestResponse,
)

_LOOPBACK_HOSTS = {
    "127.0.0.1",
    "::1",
    "localhost",
}


class _RejectRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        raise ValueError(
            "Local SUT protocol redirects are not allowed."
        )


class LocalHTTPSUTAdapter(SUTAdapter):
    """
    Local HTTP adapter for DLLO-compatible SUT endpoints.

    The adapter is intentionally restricted to loopback hosts.
    """

    def __init__(
        self,
        base_url: str,
        *,
        load_manifest: bool = True,
    ) -> None:
        normalized = base_url.rstrip("/")
        parsed = urlparse(normalized)

        if parsed.scheme not in {
            "http",
            "https",
        }:
            raise ValueError(
                "Local SUT URL must use http or https."
            )

        if parsed.hostname not in _LOOPBACK_HOSTS:
            raise ValueError(
                "Local SUT endpoint must use a localhost "
                "or loopback host."
            )

        self.base_url = normalized
        self._opener = build_opener(
            _RejectRedirectHandler()
        )

        if load_manifest:
            self.manifest = self._load_manifest()

    def _load_manifest(self):
        with self._opener.open(
            f"{self.base_url}/v1/manifest",
            timeout=5,
        ) as response:
            raw_data = json.loads(
                response.read().decode("utf-8")
            )

        payload = SUTProtocolManifestResponse.model_validate(
            raw_data
        )

        return payload.manifest

    def execute(
        self,
        context: SUTExecutionContext,
        request: SUTRequest,
    ) -> SUTExecutionResult:
        protocol_context = SUTProtocolExecutionContext(
            observer_id=context.observer_id,
            region_code=context.region_code,
            benchmark_version=context.benchmark_version,
            task_id=context.task_id,
            target_id=context.target_id,
        )

        payload = SUTProtocolExecutionRequest(
            context=protocol_context,
            task=request.task,
            metadata=request.metadata,
        )

        http_request = Request(
            f"{self.base_url}/v1/execute",
            data=payload.model_dump_json().encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        with self._opener.open(
            http_request,
            timeout=30,
        ) as response:
            raw_data = json.loads(
                response.read().decode("utf-8")
            )

        protocol_result = (
            SUTProtocolExecutionResponse.model_validate(
                raw_data
            )
        )

        result_context = SUTExecutionContext(
            observer_id=protocol_result.context.observer_id,
            region_code=protocol_result.context.region_code,
            benchmark_version=(
                protocol_result.context.benchmark_version
            ),
            task_id=protocol_result.context.task_id,
            target_id=protocol_result.context.target_id,
        )

        return SUTExecutionResult(
            context=result_context,
            started_at_utc=protocol_result.started_at_utc,
            finished_at_utc=protocol_result.finished_at_utc,
            latency_ms=protocol_result.latency_ms,
            task_completed=protocol_result.task_completed,
            output_text=protocol_result.output_text,
            retry_count=protocol_result.retry_count,
            human_intervention_count=(
                protocol_result.human_intervention_count
            ),
            error_type=protocol_result.error_type,
            metrics=protocol_result.metrics,
        )
