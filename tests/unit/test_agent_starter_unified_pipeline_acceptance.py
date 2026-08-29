from pathlib import Path

from observer.core.agent_starter_catalog_bank import (
    AgentStarterCatalogBank,
)
from observer.core.agent_starter_unified_pipeline import (
    run_agent_starter_unified_pipeline,
)
from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    AgentStarterIntake,
    EvidenceSource,
)
from schemas.compatibility import (
    AssessmentBasis,
    CompatibilityAssessment,
    CompatibilityVerdict,
)


def _compatible(
    architecture_id: str,
) -> CompatibilityAssessment:
    return CompatibilityAssessment(
        basis=AssessmentBasis.ESTIMATED,
        verdict=CompatibilityVerdict.COMPATIBLE,
        summary=(
            f"{architecture_id} is technically available "
            "for this acceptance fixture."
        ),
        confidence=0.6,
    )


def _snapshot():
    return AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    ).load_snapshot(
        "catalog-v0-1.json",
    )


def _run(
    *,
    intake: AgentStarterIntake,
    candidate_ids: list[str],
):
    return run_agent_starter_unified_pipeline(
        intake=intake,
        catalog_snapshot=_snapshot(),
        compatibility_by_architecture={
            architecture_id: _compatible(architecture_id)
            for architecture_id in candidate_ids
        },
    )


def _stacks_by_id(report):
    return {
        stack.architecture_id: stack
        for stack in (
            report.context.classification.resolution.stacks
        )
    }


def _selected_identifiers(stack) -> list[str]:
    return [
        component.selected_entry.identifier
        for component in stack.components
        if component.selected_entry is not None
    ]


def _assert_integrity(
    report,
    *,
    goal: AgentStarterGoal,
    candidate_ids: list[str],
) -> None:
    assert report.context.prepared.goal is goal

    assert (
        report.context.catalog_snapshot.snapshot_id
        == "agent-starter-catalog-v0-1"
    )
    assert (
        report.context.classification
        .resolution.catalog_result.catalog_snapshot_id
        == "agent-starter-catalog-v0-1"
    )

    assert [
        explanation.assessment.architecture_id
        for explanation in report.candidate_explanations
    ] == candidate_ids

    assert [
        stack.architecture_id
        for stack in (
            report.context.classification.resolution.stacks
        )
    ] == candidate_ids

    classified_ids = {
        *report.recommended_architecture_ids,
        *report.alternative_architecture_ids,
        *report.possible_but_not_recommended_architecture_ids,
        *report.not_recommended_architecture_ids,
    }

    assert classified_ids == set(candidate_ids)


def test_coding_runs_end_to_end_against_repository_catalog():
    candidate_ids = [
        "local-coding-agent",
        "remote-coding-agent",
    ]

    report = _run(
        intake=AgentStarterIntake(
            goal=AgentStarterGoal.CODING,
            evidence=[
                AgentStarterEvidence(
                    key="source_code_must_stay_local",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
            ],
        ),
        candidate_ids=candidate_ids,
    )

    _assert_integrity(
        report,
        goal=AgentStarterGoal.CODING,
        candidate_ids=candidate_ids,
    )

    assert report.alternative_architecture_ids == [
        "local-coding-agent",
    ]
    assert report.not_recommended_architecture_ids == [
        "remote-coding-agent",
    ]

    assert _selected_identifiers(
        _stacks_by_id(report)["local-coding-agent"]
    ) == [
        "qwen2.5-coder-7b-instruct",
    ]


def test_knowledge_runs_end_to_end_against_repository_catalog():
    candidate_ids = [
        "direct-context-knowledge-assistant",
        "full-rag-pipeline",
    ]

    report = _run(
        intake=AgentStarterIntake(
            goal=AgentStarterGoal.KNOWLEDGE_RAG,
            evidence=[
                AgentStarterEvidence(
                    key="corpus_is_very_small",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
            ],
        ),
        candidate_ids=candidate_ids,
    )

    _assert_integrity(
        report,
        goal=AgentStarterGoal.KNOWLEDGE_RAG,
        candidate_ids=candidate_ids,
    )

    assert report.recommended_architecture_ids == [
        "direct-context-knowledge-assistant",
    ]
    assert (
        report.possible_but_not_recommended_architecture_ids
        == [
            "full-rag-pipeline",
        ]
    )

    assert _selected_identifiers(
        _stacks_by_id(report)[
            "direct-context-knowledge-assistant"
        ]
    ) == [
        "qwen2.5-coder-7b-instruct",
    ]


def test_automation_runs_end_to_end_and_can_recommend_no_ai():
    candidate_ids = [
        "traditional-deterministic-automation",
        "supervised-automation-agent",
        "autonomous-workflow-agent",
    ]

    report = _run(
        intake=AgentStarterIntake(
            goal=AgentStarterGoal.AUTOMATION,
            evidence=[
                AgentStarterEvidence(
                    key="workflow_deterministic",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
            ],
        ),
        candidate_ids=candidate_ids,
    )

    _assert_integrity(
        report,
        goal=AgentStarterGoal.AUTOMATION,
        candidate_ids=candidate_ids,
    )

    assert report.recommended_architecture_ids == [
        "traditional-deterministic-automation",
    ]
    assert (
        report.possible_but_not_recommended_architecture_ids
        == [
            "supervised-automation-agent",
            "autonomous-workflow-agent",
        ]
    )

    stacks = _stacks_by_id(report)

    assert (
        stacks[
            "traditional-deterministic-automation"
        ].components
        == []
    )

    assert _selected_identifiers(
        stacks["supervised-automation-agent"]
    ) == [
        "qwen2.5-coder-7b-instruct",
    ]


def test_voice_runs_end_to_end_against_repository_catalog():
    candidate_ids = [
        "local-voice-pipeline",
        "hybrid-voice-pipeline",
        "cloud-voice-pipeline",
    ]

    report = _run(
        intake=AgentStarterIntake(
            goal=AgentStarterGoal.VOICE,
            evidence=[
                AgentStarterEvidence(
                    key="raw_audio_must_stay_local",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
                AgentStarterEvidence(
                    key="transcript_must_stay_local",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
            ],
        ),
        candidate_ids=candidate_ids,
    )

    _assert_integrity(
        report,
        goal=AgentStarterGoal.VOICE,
        candidate_ids=candidate_ids,
    )

    assert report.alternative_architecture_ids == [
        "local-voice-pipeline",
    ]
    assert report.not_recommended_architecture_ids == [
        "hybrid-voice-pipeline",
        "cloud-voice-pipeline",
    ]

    assert _selected_identifiers(
        _stacks_by_id(report)["local-voice-pipeline"]
    ) == [
        "whisper.cpp-v1.9.2",
        "kokoro-82m-v1.0",
    ]


def test_personal_runs_end_to_end_against_repository_catalog():
    candidate_ids = [
        "session-only-personal-assistant",
        "opaque-persistent-memory-assistant",
        "controlled-persistent-memory-assistant",
    ]

    report = _run(
        intake=AgentStarterIntake(
            goal=AgentStarterGoal.PERSONAL,
            evidence=[
                AgentStarterEvidence(
                    key="cross_session_memory_required",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
            ],
        ),
        candidate_ids=candidate_ids,
    )

    _assert_integrity(
        report,
        goal=AgentStarterGoal.PERSONAL,
        candidate_ids=candidate_ids,
    )

    assert [
        capability.key
        for capability in report.requested_capabilities
    ] == [
        "persistent_memory_required",
    ]

    assert report.alternative_architecture_ids == [
        "opaque-persistent-memory-assistant",
        "controlled-persistent-memory-assistant",
    ]
    assert report.not_recommended_architecture_ids == [
        "session-only-personal-assistant",
    ]

    assert _selected_identifiers(
        _stacks_by_id(report)[
            "controlled-persistent-memory-assistant"
        ]
    ) == [
        "qwen2.5-coder-7b-instruct",
    ]


def test_coding_hardware_profile_reaches_final_catalog_stack():
    from datetime import datetime, timezone

    from schemas.agent_starter_catalog import (
        AgentStarterCatalogEntry,
        AgentStarterCatalogSnapshot,
    )
    from schemas.hardware import (
        DeviceClass,
        HardwareProfile,
        HardwareProfileSource,
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=8 * 1024**3,
    )

    def local_model(
        identifier: str,
        *,
        parameter_count: int | None = None,
        quantization: str | None = None,
    ) -> AgentStarterCatalogEntry:
        model_profile = None

        if parameter_count is not None or quantization is not None:
            model_profile = {
                "model_id": identifier,
                "parameter_count": parameter_count,
                "quantization": quantization,
                "execution_location": "on_device",
            }

        return AgentStarterCatalogEntry.model_validate(
            {
                "schema_version": "0.2",
                "identifier": identifier,
                "component_type": "llm",
                "vendor": "Example Vendor",
                "family": "Example",
                "version": "1.0",
                "capabilities": [
                    "coding",
                ],
                "deployment_modes": [
                    "on_device",
                ],
                "license": "example-license",
                "pricing_class": "free",
                "access_options": [
                    {
                        "deployment_mode": "on_device",
                        "access_kind": "self_hosted",
                        "pricing": "free",
                        "model_profile": model_profile,
                    },
                ],
                "sources": [
                    f"https://example.invalid/{identifier}",
                ],
                "verified_at": datetime(
                    2026,
                    8,
                    29,
                    tzinfo=timezone.utc,
                ),
            }
        )

    compatible = local_model(
        "local-3b-q4",
        parameter_count=3_000_000_000,
        quantization="q4",
    )
    constrained = local_model(
        "local-7b-q4",
        parameter_count=7_000_000_000,
        quantization="q4",
    )
    unknown = local_model(
        "local-unknown",
    )
    not_recommended = local_model(
        "local-30b-q4",
        parameter_count=30_000_000_000,
        quantization="q4",
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-hardware-acceptance",
        generated_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
        entries=[
            compatible,
            constrained,
            unknown,
            not_recommended,
        ],
    )

    candidate_ids = [
        "local-coding-agent",
        "remote-coding-agent",
    ]

    report = run_agent_starter_unified_pipeline(
        intake=AgentStarterIntake(
            goal=AgentStarterGoal.CODING,
            evidence=[
                AgentStarterEvidence(
                    key="source_code_must_stay_local",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
            ],
            hardware_profile=hardware,
        ),
        catalog_snapshot=snapshot,
        compatibility_by_architecture={
            architecture_id: _compatible(architecture_id)
            for architecture_id in candidate_ids
        },
    )

    assert report.context.prepared.hardware_profile == hardware

    stack = _stacks_by_id(report)["local-coding-agent"]

    assert len(stack.components) == 1

    component = stack.components[0]

    assert [
        entry.identifier
        for entry in component.matched_entries
    ] == [
        "local-3b-q4",
    ]

    assert [
        entry.identifier
        for entry in component.constrained_entries
    ] == [
        "local-7b-q4",
    ]

    assert [
        entry.identifier
        for entry in component.indeterminate_entries
    ] == [
        "local-unknown",
    ]

    assert [
        entry.identifier
        for entry in component.not_recommended_entries
    ] == [
        "local-30b-q4",
    ]

    assert component.constraint_excluded_entries == []

    assert component.selected_entry == compatible


def test_mobile_android_runtime_inventory_reaches_repository_catalog_v0_2():
    from schemas.execution_environment import (
        ExecutionEnvironment,
        ExecutionInterface,
        ExecutionPlatform,
    )
    from schemas.hardware import (
        DeviceClass,
        HardwareProfile,
        HardwareProfileSource,
    )

    snapshot = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    ).load_snapshot(
        "catalog-v0-2.json",
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.PHONE,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=4 * 1024**3,
    )

    environment = ExecutionEnvironment(
        platform=ExecutionPlatform.ANDROID,
        interface=ExecutionInterface.NATIVE,
        available_runtimes=[
            "llama.cpp",
        ],
    )

    candidate_ids = [
        "local-coding-agent",
        "remote-coding-agent",
    ]

    report = run_agent_starter_unified_pipeline(
        intake=AgentStarterIntake(
            goal=AgentStarterGoal.CODING,
            evidence=[
                AgentStarterEvidence(
                    key="source_code_must_stay_local",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
            ],
            hardware_profile=hardware,
            execution_environment=environment,
        ),
        catalog_snapshot=snapshot,
        compatibility_by_architecture={
            architecture_id: _compatible(architecture_id)
            for architecture_id in candidate_ids
        },
    )

    assert report.context.prepared.hardware_profile == hardware
    assert (
        report.context.prepared.execution_environment
        == environment
    )

    assert (
        report.context.catalog_snapshot.snapshot_id
        == "agent-starter-catalog-v0-2"
    )

    stack = _stacks_by_id(report)["local-coding-agent"]

    assert len(stack.components) == 1

    component = stack.components[0]

    assert component.matched_entries == []
    assert component.constrained_entries == []
    assert component.indeterminate_entries == []
    assert component.constraint_excluded_entries == []

    assert [
        entry.identifier
        for entry in component.not_recommended_entries
    ] == [
        "qwen3-0.6b",
        "gemma-3-1b-it",
        "llama-3.2-1b-instruct",
        "qwen3-1.7b",
        "granite-3.3-2b-instruct",
        "qwen3-coder-30b-a3b-instruct",
        "gemma-4-e4b-it",
        "gpt-oss-20b",
        "phi-4-mini-instruct",
        "granite-4.0-h-micro",
        "nvidia-nemotron-nano-9b-v2",
    ]

    assert component.selected_entry is None


def test_mobile_ios_unknown_runtime_inventory_stays_indeterminate():
    from schemas.execution_environment import (
        ExecutionEnvironment,
        ExecutionInterface,
        ExecutionPlatform,
    )
    from schemas.hardware import (
        DeviceClass,
        HardwareProfile,
        HardwareProfileSource,
    )

    snapshot = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    ).load_snapshot(
        "catalog-v0-2.json",
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.PHONE,
        source=HardwareProfileSource.BROWSER_LIMITED,
        total_memory_bytes=None,
        limitations=[
            "Browser access does not expose complete hardware information.",
        ],
    )

    environment = ExecutionEnvironment(
        platform=ExecutionPlatform.IOS,
        interface=ExecutionInterface.BROWSER,
        available_runtimes=None,
        limitations=[
            "Runtime inventory is not observable from this browser session.",
        ],
    )

    candidate_ids = [
        "local-coding-agent",
        "remote-coding-agent",
    ]

    report = run_agent_starter_unified_pipeline(
        intake=AgentStarterIntake(
            goal=AgentStarterGoal.CODING,
            evidence=[
                AgentStarterEvidence(
                    key="source_code_must_stay_local",
                    source=EvidenceSource.DECLARED,
                    value=True,
                ),
            ],
            hardware_profile=hardware,
            execution_environment=environment,
        ),
        catalog_snapshot=snapshot,
        compatibility_by_architecture={
            architecture_id: _compatible(architecture_id)
            for architecture_id in candidate_ids
        },
    )

    assert report.context.prepared.hardware_profile == hardware
    assert (
        report.context.prepared.execution_environment
        == environment
    )

    stack = _stacks_by_id(report)["local-coding-agent"]

    assert len(stack.components) == 1

    component = stack.components[0]

    assert component.matched_entries == []
    assert component.constrained_entries == []
    assert component.not_recommended_entries == []
    assert component.constraint_excluded_entries == []

    assert [
        entry.identifier
        for entry in component.indeterminate_entries
    ] == [
        "qwen3-0.6b",
        "gemma-3-1b-it",
        "llama-3.2-1b-instruct",
        "qwen3-1.7b",
        "granite-3.3-2b-instruct",
        "qwen3-coder-30b-a3b-instruct",
        "gemma-4-e4b-it",
        "gpt-oss-20b",
        "phi-4-mini-instruct",
        "granite-4.0-h-micro",
        "nvidia-nemotron-nano-9b-v2",
    ]

    assert component.selected_entry is None
