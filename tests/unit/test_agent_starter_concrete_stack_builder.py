from datetime import datetime, timezone

import pytest

from schemas.agent_starter import (
    AgentStarterEvidence,
    AgentStarterGoal,
    CandidateArchitectureAssessment,
    EvidenceSource,
    RecommendationConfidence,
    RecommendationVerdict,
    TechnicalFeasibility,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogArchitectureResult,
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
    AgentStarterCatalogQuery,
    AgentStarterCatalogQueryMatch,
)


def _coding_assessment() -> CandidateArchitectureAssessment:
    return CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding architecture requires "
                    "a language model."
                ),
            ),
        ],
    )


def _entry(identifier: str) -> AgentStarterCatalogEntry:
    return AgentStarterCatalogEntry(
        identifier=identifier,
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="test-vendor",
        family="test-family",
        version="1.0",
        capabilities=[
            "coding",
        ],
        license="test-license",
        pricing_class="free",
        sources=[
            "https://example.com/catalog-entry",
        ],
        verified_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
    )


def _architecture_result(
    matched_entries: list[AgentStarterCatalogEntry],
) -> AgentStarterCatalogArchitectureResult:
    query = AgentStarterCatalogQuery(
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "coding",
        ],
    )

    return AgentStarterCatalogArchitectureResult(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        query_matches=[
            AgentStarterCatalogQueryMatch(
                architecture_id="local-coding-agent",
                catalog_snapshot_id=(
                    "agent-starter-catalog-v0-1"
                ),
                query=query,
                matched_entries=matched_entries,
            ),
        ],
    )


def test_concrete_stack_builder_selects_unique_catalog_match():
    from observer.core.agent_starter_concrete_stack_builder import (
        build_agent_starter_concrete_stack,
    )

    entry = _entry("coding-model-a")

    stack = build_agent_starter_concrete_stack(
        goal=AgentStarterGoal.CODING,
        assessment=_coding_assessment(),
        architecture_result=_architecture_result(
            [
                entry,
            ]
        ),
    )

    assert stack.architecture_id == "local-coding-agent"
    assert (
        stack.catalog_snapshot_id
        == "agent-starter-catalog-v0-1"
    )
    assert len(stack.components) == 1

    component = stack.components[0]

    assert (
        component.requirement.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert component.requirement.required_capabilities == [
        "coding",
    ]
    assert component.matched_entries == [entry]
    assert component.selected_entry == entry


def test_concrete_stack_builder_preserves_zero_match():
    from observer.core.agent_starter_concrete_stack_builder import (
        build_agent_starter_concrete_stack,
    )

    stack = build_agent_starter_concrete_stack(
        goal=AgentStarterGoal.CODING,
        assessment=_coding_assessment(),
        architecture_result=_architecture_result([]),
    )

    component = stack.components[0]

    assert component.matched_entries == []
    assert component.selected_entry is None


def test_concrete_stack_builder_does_not_choose_between_multiple_matches():
    from observer.core.agent_starter_concrete_stack_builder import (
        build_agent_starter_concrete_stack,
    )

    first = _entry("coding-model-a")
    second = _entry("coding-model-b")

    stack = build_agent_starter_concrete_stack(
        goal=AgentStarterGoal.CODING,
        assessment=_coding_assessment(),
        architecture_result=_architecture_result(
            [
                first,
                second,
            ]
        ),
    )

    component = stack.components[0]

    assert component.matched_entries == [
        first,
        second,
    ]
    assert component.selected_entry is None


def test_concrete_stack_builder_rejects_catalog_query_not_matching_requirement():
    from observer.core.agent_starter_concrete_stack_builder import (
        build_agent_starter_concrete_stack,
    )

    mismatched_result = AgentStarterCatalogArchitectureResult(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        query_matches=[
            AgentStarterCatalogQueryMatch(
                architecture_id="local-coding-agent",
                catalog_snapshot_id=(
                    "agent-starter-catalog-v0-1"
                ),
                query=AgentStarterCatalogQuery(
                    component_type=(
                        AgentStarterCatalogComponentType.LLM
                    ),
                    required_capabilities=[],
                ),
                matched_entries=[],
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="catalog query does not match",
    ):
        build_agent_starter_concrete_stack(
            goal=AgentStarterGoal.CODING,
            assessment=_coding_assessment(),
            architecture_result=mismatched_result,
        )


def test_concrete_stack_builder_composes_voice_stt_and_tts_components():
    from observer.core.agent_starter_concrete_stack_builder import (
        build_agent_starter_concrete_stack,
    )

    voice_assessment = CandidateArchitectureAssessment(
        architecture_id="hybrid-voice-pipeline",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The voice architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The voice architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_stt",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice architecture requires "
                    "speech-to-text."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_tts",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice architecture requires "
                    "text-to-speech."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_raw_audio_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Raw audio remains in the "
                    "user-controlled environment."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_transcript_remote_processing",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "Transcript processing may occur remotely."
                ),
            ),
        ],
    )

    stt_entry = AgentStarterCatalogEntry(
        identifier="stt-a",
        component_type=AgentStarterCatalogComponentType.STT,
        vendor="test-vendor",
        family="test-stt",
        version="1.0",
        license="test-license",
        pricing_class="free",
        sources=[
            "https://example.com/stt",
        ],
        verified_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
    )

    tts_entry = AgentStarterCatalogEntry(
        identifier="tts-a",
        component_type=AgentStarterCatalogComponentType.TTS,
        vendor="test-vendor",
        family="test-tts",
        version="1.0",
        license="test-license",
        pricing_class="free",
        sources=[
            "https://example.com/tts",
        ],
        verified_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
    )

    architecture_result = AgentStarterCatalogArchitectureResult(
        architecture_id="hybrid-voice-pipeline",
        catalog_snapshot_id="agent-starter-catalog-v0-1",
        query_matches=[
            AgentStarterCatalogQueryMatch(
                architecture_id="hybrid-voice-pipeline",
                catalog_snapshot_id=(
                    "agent-starter-catalog-v0-1"
                ),
                query=AgentStarterCatalogQuery(
                    component_type=(
                        AgentStarterCatalogComponentType.STT
                    ),
                ),
                matched_entries=[
                    stt_entry,
                ],
            ),
            AgentStarterCatalogQueryMatch(
                architecture_id="hybrid-voice-pipeline",
                catalog_snapshot_id=(
                    "agent-starter-catalog-v0-1"
                ),
                query=AgentStarterCatalogQuery(
                    component_type=(
                        AgentStarterCatalogComponentType.TTS
                    ),
                ),
                matched_entries=[
                    tts_entry,
                ],
            ),
        ],
    )

    stack = build_agent_starter_concrete_stack(
        goal=AgentStarterGoal.VOICE,
        assessment=voice_assessment,
        architecture_result=architecture_result,
    )

    assert [
        component.requirement.component_type
        for component in stack.components
    ] == [
        AgentStarterCatalogComponentType.STT,
        AgentStarterCatalogComponentType.TTS,
    ]

    assert [
        component.selected_entry.identifier
        for component in stack.components
        if component.selected_entry is not None
    ] == [
        "stt-a",
        "tts-a",
    ]


def test_concrete_stack_builder_preserves_non_matching_result_classes():
    from datetime import datetime, timezone

    from observer.core.agent_starter_concrete_stack_builder import (
        build_agent_starter_concrete_stack,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterGoal,
        CandidateArchitectureAssessment,
        EvidenceSource,
        RecommendationConfidence,
        RecommendationVerdict,
        TechnicalFeasibility,
    )
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogArchitectureResult,
        AgentStarterCatalogComponentType,
        AgentStarterCatalogEntry,
        AgentStarterCatalogQuery,
        AgentStarterCatalogQueryMatch,
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="local-coding-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The coding architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The coding architecture satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding architecture requires "
                    "a language model."
                ),
            ),
        ],
    )

    def entry(identifier: str) -> AgentStarterCatalogEntry:
        return AgentStarterCatalogEntry(
            identifier=identifier,
            component_type=AgentStarterCatalogComponentType.LLM,
            vendor="Example Vendor",
            family="Example",
            version="1.0",
            capabilities=[
                "coding",
            ],
            license="example-license",
            pricing_class="free",
            sources=[
                f"https://example.invalid/{identifier}",
            ],
            verified_at=datetime(
                2026,
                8,
                29,
                tzinfo=timezone.utc,
            ),
        )

    constrained = entry(
        "constrained-model",
    )
    indeterminate = entry(
        "unknown-cost-model",
    )
    not_recommended = entry(
        "not-recommended-model",
    )
    excluded = entry(
        "paid-service-model",
    )

    architecture_result = AgentStarterCatalogArchitectureResult(
        architecture_id="local-coding-agent",
        catalog_snapshot_id="catalog-v0-2-test",
        query_matches=[
            AgentStarterCatalogQueryMatch(
                architecture_id="local-coding-agent",
                catalog_snapshot_id="catalog-v0-2-test",
                query=AgentStarterCatalogQuery(
                    component_type=(
                        AgentStarterCatalogComponentType.LLM
                    ),
                    required_capabilities=[
                        "coding",
                    ],
                ),
                matched_entries=[],
                constrained_entries=[
                    constrained,
                ],
                indeterminate_entries=[
                    indeterminate,
                ],
                not_recommended_entries=[
                    not_recommended,
                ],
                constraint_excluded_entries=[
                    excluded,
                ],
            ),
        ],
    )

    stack = build_agent_starter_concrete_stack(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
        architecture_result=architecture_result,
    )

    component = stack.components[0]

    assert component.constrained_entries == [
        constrained,
    ]
    assert component.not_recommended_entries == [
        not_recommended,
    ]

    assert component.matched_entries == []
    assert component.indeterminate_entries == [
        indeterminate,
    ]
    assert component.constraint_excluded_entries == [
        excluded,
    ]
    assert component.selected_entry is None
