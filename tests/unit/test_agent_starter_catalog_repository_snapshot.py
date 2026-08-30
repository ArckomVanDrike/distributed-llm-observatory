from pathlib import Path

from observer.core.agent_starter_catalog_bank import (
    AgentStarterCatalogBank,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
)


def test_repository_catalog_v0_1_loads_as_explicit_snapshot():
    bank = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    )

    snapshot = bank.load_snapshot(
        "catalog-v0-1.json",
    )

    assert snapshot.snapshot_id == "agent-starter-catalog-v0-1"

    assert [
        entry.identifier
        for entry in snapshot.entries
    ] == [
        "qwen2.5-coder-7b-instruct",
        "ollama-v0.33.1",
        "whisper.cpp-v1.9.2",
        "kokoro-82m-v1.0",
    ]

    assert [
        entry.component_type
        for entry in snapshot.entries
    ] == [
        AgentStarterCatalogComponentType.LLM,
        AgentStarterCatalogComponentType.RUNTIME,
        AgentStarterCatalogComponentType.STT,
        AgentStarterCatalogComponentType.TTS,
    ]


def test_repository_catalog_matches_coding_through_catalog_pipeline():
    from observer.core.agent_starter_catalog_pipeline import (
        run_agent_starter_catalog_matching,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterGoal,
        AgentStarterPlan,
        CandidateArchitectureAssessment,
        EvidenceSource,
        RecommendationConfidence,
        RecommendationVerdict,
        TechnicalFeasibility,
    )

    bank = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    )
    snapshot = bank.load_snapshot(
        "catalog-v0-1.json",
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
                    "The coding-agent architecture uses an LLM "
                    "for coding assistance."
                ),
            ),
            AgentStarterEvidence(
                key="source_code_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Source code remains inside the "
                    "user-controlled environment."
                ),
            ),
        ],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=[
            assessment,
        ],
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    architecture_result = result.architecture_results[0]

    assert architecture_result.architecture_id == (
        "local-coding-agent"
    )
    assert len(architecture_result.query_matches) == 1

    query_match = architecture_result.query_matches[0]

    assert (
        query_match.query.component_type
        is AgentStarterCatalogComponentType.LLM
    )
    assert query_match.query.required_capabilities == [
        "coding",
    ]

    # "Local" architecture provenance is not sufficient
    # to infer a concrete deployment mode.
    assert query_match.query.required_deployment_modes == []

    assert [
        entry.identifier
        for entry in query_match.matched_entries
    ] == [
        "qwen2.5-coder-7b-instruct",
    ]


def test_repository_catalog_matches_voice_through_catalog_pipeline():
    from observer.core.agent_starter_catalog_pipeline import (
        run_agent_starter_catalog_matching,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterGoal,
        AgentStarterPlan,
        CandidateArchitectureAssessment,
        EvidenceSource,
        RecommendationConfidence,
        RecommendationVerdict,
        TechnicalFeasibility,
    )

    bank = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    )
    snapshot = bank.load_snapshot(
        "catalog-v0-1.json",
    )

    assessment = CandidateArchitectureAssessment(
        architecture_id="local-voice-pipeline",
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
                    "The voice-pipeline architecture uses speech-to-text "
                    "for speech input processing."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_tts",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The voice-pipeline architecture uses text-to-speech "
                    "for speech output generation."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_raw_audio_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Raw audio remains inside the "
                    "user-controlled environment."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_transcript_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Transcripts remain inside the "
                    "user-controlled environment."
                ),
            ),
        ],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.VOICE,
        requirements=[],
        candidate_assessments=[
            assessment,
        ],
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    architecture_result = result.architecture_results[0]

    assert architecture_result.architecture_id == (
        "local-voice-pipeline"
    )

    assert [
        match.query.component_type
        for match in architecture_result.query_matches
    ] == [
        AgentStarterCatalogComponentType.STT,
        AgentStarterCatalogComponentType.TTS,
    ]

    assert all(
        match.query.required_deployment_modes == []
        for match in architecture_result.query_matches
    )

    stt_match, tts_match = architecture_result.query_matches

    assert [
        entry.identifier
        for entry in stt_match.matched_entries
    ] == [
        "whisper.cpp-v1.9.2",
    ]

    assert [
        entry.identifier
        for entry in tts_match.matched_entries
    ] == [
        "kokoro-82m-v1.0",
    ]


def test_repository_catalog_v0_2_loads_as_explicit_snapshot():
    bank = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    )

    snapshot = bank.load_snapshot(
        "catalog-v0-2.json",
    )

    assert snapshot.schema_version == "0.2"
    assert (
        snapshot.snapshot_id
        == "agent-starter-catalog-v0-2"
    )

    assert [
        entry.identifier
        for entry in snapshot.entries
    ] == [
        "gemma-3-270m-it",
        "qwen3-0.6b",
        "gemma-3-1b-it",
        "llama-3.2-1b-instruct",
        "qwen3-1.7b",
        "granite-3.3-2b-instruct",
        "qwen3-coder-30b-a3b-instruct",
        "gemma-4-e4b-it",
        "ministral-3-8b-instruct-2512",
        "gpt-oss-20b",
        "phi-4-mini-instruct",
        "granite-4.0-h-micro",
        "nvidia-nemotron-nano-9b-v2",
        "qwen3-embedding-0.6b",
        "bge-m3",
        "parakeet-tdt-0.6b-v3",
        "voxtral-mini-3b-2507",
        "whisper.cpp-v1.9.2",
        "kokoro-82m-v1.0",
        "llama.cpp-b10516",
    ]

    assert all(
        entry.schema_version == "0.2"
        for entry in snapshot.entries
    )

    assert all(
        entry.access_options
        for entry in snapshot.entries
    )

    assert all(
        option.deployment_mode in entry.deployment_modes
        for entry in snapshot.entries
        for option in entry.access_options
    )


def test_repository_catalog_v0_2_preserves_verified_semantics():
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogLicenseCost,
    )

    snapshot = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    ).load_snapshot(
        "catalog-v0-2.json",
    )

    entries = {
        entry.identifier: entry
        for entry in snapshot.entries
    }

    gpt_oss = entries["gpt-oss-20b"]

    assert "coding" in gpt_oss.capabilities
    assert (
        gpt_oss.access_options[0]
        .model_profile
        .quantization
        == "mxfp4"
    )

    ministral = entries[
        "ministral-3-8b-instruct-2512"
    ]

    assert (
        ministral.access_options[0]
        .model_profile
        .quantization
        == "fp8"
    )

    nemotron = entries[
        "nvidia-nemotron-nano-9b-v2"
    ]

    assert (
        nemotron.license_cost
        is AgentStarterCatalogLicenseCost.FREE
    )

    assert (
        "https://www.nvidia.com/en-us/agreements/"
        "enterprise-software/nvidia-open-model-license/"
        in nemotron.sources
    )


def test_repository_catalog_v0_2_classifies_coding_with_16_gib():
    from observer.core.agent_starter_catalog_pipeline import (
        run_agent_starter_catalog_matching,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterGoal,
        AgentStarterPlan,
        CandidateArchitectureAssessment,
        EvidenceSource,
        RecommendationConfidence,
        RecommendationVerdict,
        TechnicalFeasibility,
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

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=[
            assessment,
        ],
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=16 * 1024**3,
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
        hardware_profile=hardware,
    )

    query_match = (
        result.architecture_results[0]
        .query_matches[0]
    )

    assert query_match.query.required_capabilities == [
        "coding",
    ]

    assert [
        entry.identifier
        for entry in query_match.matched_entries
    ] == [
        "qwen3-0.6b",
        "gemma-3-1b-it",
        "llama-3.2-1b-instruct",
        "qwen3-1.7b",
        "granite-3.3-2b-instruct",
        "granite-4.0-h-micro",
    ]

    assert [
        entry.identifier
        for entry in query_match.constrained_entries
    ] == [
        "phi-4-mini-instruct",
    ]

    assert [
        entry.identifier
        for entry in query_match.indeterminate_entries
    ] == [
        "gemma-4-e4b-it",
        "gpt-oss-20b",
    ]

    assert [
        entry.identifier
        for entry in query_match.not_recommended_entries
    ] == [
        "qwen3-coder-30b-a3b-instruct",
        "nvidia-nemotron-nano-9b-v2",
    ]

    assert query_match.constraint_excluded_entries == []

    classified_ids = {
        entry.identifier
        for entries in (
            query_match.matched_entries,
            query_match.constrained_entries,
            query_match.indeterminate_entries,
            query_match.not_recommended_entries,
            query_match.constraint_excluded_entries,
        )
        for entry in entries
    }

    assert classified_ids == {
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
    }


def test_repository_catalog_v0_2_includes_low_resource_models():
    snapshot = AgentStarterCatalogBank(
        root=Path("catalog/agent-starter"),
    ).load_snapshot(
        "catalog-v0-2.json",
    )

    identifiers = {
        entry.identifier
        for entry in snapshot.entries
    }

    assert {
        "gemma-3-270m-it",
        "qwen3-0.6b",
        "gemma-3-1b-it",
        "llama-3.2-1b-instruct",
        "qwen3-1.7b",
        "granite-3.3-2b-instruct",
    }.issubset(identifiers)


def _repository_v0_2_coding_match(
    memory_gib: int,
):
    from observer.core.agent_starter_catalog_pipeline import (
        run_agent_starter_catalog_matching,
    )
    from schemas.agent_starter import (
        AgentStarterEvidence,
        AgentStarterGoal,
        AgentStarterPlan,
        CandidateArchitectureAssessment,
        EvidenceSource,
        RecommendationConfidence,
        RecommendationVerdict,
        TechnicalFeasibility,
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

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[],
        candidate_assessments=[
            assessment,
        ],
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=memory_gib * 1024**3,
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
        hardware_profile=hardware,
    )

    return (
        result.architecture_results[0]
        .query_matches[0]
    )


def test_repository_catalog_v0_2_coding_on_2_gib():
    query_match = _repository_v0_2_coding_match(2)

    assert query_match.matched_entries == []

    assert [
        entry.identifier
        for entry in query_match.constrained_entries
    ] == [
        "qwen3-0.6b",
    ]

    assert [
        entry.identifier
        for entry in query_match.indeterminate_entries
    ] == [
        "gemma-4-e4b-it",
        "gpt-oss-20b",
    ]

    assert [
        entry.identifier
        for entry in query_match.not_recommended_entries
    ] == [
        "gemma-3-1b-it",
        "llama-3.2-1b-instruct",
        "qwen3-1.7b",
        "granite-3.3-2b-instruct",
        "qwen3-coder-30b-a3b-instruct",
        "phi-4-mini-instruct",
        "granite-4.0-h-micro",
        "nvidia-nemotron-nano-9b-v2",
    ]

    assert query_match.constraint_excluded_entries == []


def test_repository_catalog_v0_2_general_llm_on_2_gib():
    from observer.core.agent_starter_catalog_orchestrator import (
        _classify_local_hardware_compatibility,
    )
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogComponentType,
        AgentStarterCatalogQuery,
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

    entries = [
        entry
        for entry in snapshot.entries
        if (
            entry.component_type
            is AgentStarterCatalogComponentType.LLM
            and "text_generation" in entry.capabilities
        )
    ]

    query = AgentStarterCatalogQuery(
        component_type=AgentStarterCatalogComponentType.LLM,
        required_capabilities=[
            "text_generation",
        ],
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=2 * 1024**3,
    )

    (
        matched,
        constrained,
        indeterminate,
        not_recommended,
    ) = _classify_local_hardware_compatibility(
        entries,
        query=query,
        hardware=hardware,
    )

    assert [
        entry.identifier
        for entry in matched
    ] == [
        "gemma-3-270m-it",
    ]

    assert [
        entry.identifier
        for entry in constrained
    ] == [
        "qwen3-0.6b",
    ]

    assert [
        entry.identifier
        for entry in indeterminate
    ] == [
        "gemma-4-e4b-it",
        "ministral-3-8b-instruct-2512",
        "gpt-oss-20b",
    ]

    assert [
        entry.identifier
        for entry in not_recommended
    ] == [
        "gemma-3-1b-it",
        "llama-3.2-1b-instruct",
        "qwen3-1.7b",
        "granite-3.3-2b-instruct",
        "qwen3-coder-30b-a3b-instruct",
        "phi-4-mini-instruct",
        "granite-4.0-h-micro",
        "nvidia-nemotron-nano-9b-v2",
    ]
