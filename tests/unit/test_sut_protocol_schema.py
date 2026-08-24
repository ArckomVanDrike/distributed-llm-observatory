from datetime import datetime, timezone

from schemas.sut_protocol import (
    SUTProtocolExecutionContext,
    SUTProtocolExecutionRequest,
    SUTProtocolExecutionResponse,
    SUTProtocolManifestResponse,
)
from schemas.target import (
    TargetCapability,
    TargetManifest,
    TargetType,
)


def test_protocol_manifest_carries_target_manifest():
    response = SUTProtocolManifestResponse(
        manifest=TargetManifest(
            target_id="custom-agent",
            display_name="Custom Agent",
            target_type=TargetType.AGENT,
            capabilities={
                TargetCapability.TEXT,
                TargetCapability.FILESYSTEM,
            },
        ),
    )

    assert response.schema_version == "0.1"
    assert response.manifest.target_id == "custom-agent"
    assert TargetCapability.FILESYSTEM in response.manifest.capabilities


def test_protocol_execution_request_carries_task_context():
    context = SUTProtocolExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-filesystem-001",
        target_id="custom-agent",
    )

    request = SUTProtocolExecutionRequest(
        context=context,
        task="Create the requested file.",
        metadata={
            "experiment_id": "exp-001",
        },
    )

    assert request.schema_version == "0.1"
    assert request.context == context
    assert request.task == "Create the requested file."
    assert request.metadata == {
        "experiment_id": "exp-001",
    }


def test_protocol_execution_response_carries_result():
    now = datetime.now(timezone.utc)

    context = SUTProtocolExecutionContext(
        observer_id="observer-test",
        region_code="CL-Los-Lagos",
        benchmark_version="0.1",
        task_id="agent-filesystem-001",
        target_id="custom-agent",
    )

    response = SUTProtocolExecutionResponse(
        context=context,
        started_at_utc=now,
        finished_at_utc=now,
        latency_ms=12.5,
        task_completed=True,
        output_text="done",
        retry_count=1,
        human_intervention_count=0,
        metrics={
            "tool_calls": 2,
        },
    )

    assert response.schema_version == "0.1"
    assert response.task_completed is True
    assert response.latency_ms == 12.5
    assert response.retry_count == 1
    assert response.metrics["tool_calls"] == 2
