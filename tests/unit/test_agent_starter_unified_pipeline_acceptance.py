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
