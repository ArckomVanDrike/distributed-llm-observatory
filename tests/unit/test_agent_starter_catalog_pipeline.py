from datetime import datetime, timezone

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
from schemas.agent_starter_catalog import (
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
    AgentStarterCatalogSnapshot,
)


def test_catalog_pipeline_matches_all_plan_candidates_without_filtering():
    deterministic = CandidateArchitectureAssessment(
        architecture_id="traditional-deterministic-automation",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.RECOMMENDED,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The deterministic architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "Deterministic automation satisfies the requirements.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=False,
                reason="The candidate does not use an LLM.",
            ),
        ],
    )

    llm_automation = CandidateArchitectureAssessment(
        architecture_id="supervised-automation-agent",
        technical_feasibility=TechnicalFeasibility.FEASIBLE,
        recommendation=RecommendationVerdict.POSSIBLE,
        confidence=RecommendationConfidence.HIGH,
        technical_reasons=[
            "The LLM architecture is technically feasible.",
        ],
        recommendation_reasons=[
            "The LLM architecture is a possible alternative.",
        ],
        supporting_evidence=[
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason="The candidate uses an LLM.",
            ),
        ],
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.AUTOMATION,
        requirements=[],
        candidate_assessments=[
            deterministic,
            llm_automation,
        ],
    )

    catalog_entry = AgentStarterCatalogEntry(
        identifier="automation-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/automation-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[catalog_entry],
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    assert result.plan == plan
    assert result.catalog_snapshot_id == "catalog-2026-08-28"

    assert [
        architecture.architecture_id
        for architecture in result.architecture_results
    ] == [
        "traditional-deterministic-automation",
        "supervised-automation-agent",
    ]

    assert result.architecture_results[0].query_matches == []

    llm_matches = (
        result.architecture_results[1]
        .query_matches[0]
        .matched_entries
    )

    assert [
        entry.identifier
        for entry in llm_matches
    ] == [
        "automation-model",
    ]


def test_catalog_pipeline_preserves_coding_query_with_zero_matches():
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
        candidate_assessments=[assessment],
    )

    non_matching_entry = AgentStarterCatalogEntry(
        identifier="general-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=[
            "general_chat",
        ],
        license="example-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/general-model",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[
            non_matching_entry,
        ],
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    assert len(result.architecture_results) == 1

    architecture_result = result.architecture_results[0]

    assert architecture_result.architecture_id == "local-coding-agent"
    assert len(architecture_result.query_matches) == 1

    query_match = architecture_result.query_matches[0]

    assert query_match.query.required_capabilities == [
        "coding",
    ]
    assert query_match.matched_entries == []


def test_catalog_pipeline_applies_free_only_plan_requirement():
    from schemas.agent_starter import (
        AgentStarterRequirement,
        ConstraintStrength,
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

    free_evidence = AgentStarterEvidence(
        key="free_components_only",
        source=EvidenceSource.DECLARED,
        value=True,
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[
            AgentStarterRequirement(
                key="free_components_only",
                value=True,
                strength=ConstraintStrength.HARD,
                evidence=[
                    free_evidence,
                ],
            ),
        ],
        candidate_assessments=[
            assessment,
        ],
    )

    free_model = AgentStarterCatalogEntry(
        identifier="free-coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Free Example",
        version="1.0",
        capabilities=[
            "coding",
        ],
        license="example-free-license",
        pricing_class="free",
        sources=[
            "https://example.invalid/free-coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
    )

    paid_model = AgentStarterCatalogEntry(
        identifier="paid-coding-model",
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Paid Example",
        version="1.0",
        capabilities=[
            "coding",
        ],
        license="example-paid-license",
        pricing_class="paid",
        sources=[
            "https://example.invalid/paid-coding-model",
        ],
        verified_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-free-only-test",
        generated_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
        entries=[
            paid_model,
            free_model,
        ],
    )

    result = run_agent_starter_catalog_matching(
        plan=plan,
        snapshot=snapshot,
    )

    query_match = (
        result.architecture_results[0]
        .query_matches[0]
    )

    assert query_match.query.required_pricing_class == "free"

    assert [
        entry.identifier
        for entry in query_match.matched_entries
    ] == [
        "free-coding-model",
    ]


def test_catalog_pipeline_composes_cost_and_hardware_classification():
    from schemas.agent_starter import (
        AgentStarterRequirement,
        ConstraintStrength,
    )
    from schemas.hardware import (
        DeviceClass,
        HardwareProfile,
        HardwareProfileSource,
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

    paid_external_evidence = AgentStarterEvidence(
        key="paid_external_services_allowed",
        source=EvidenceSource.DECLARED,
        value=False,
    )

    plan = AgentStarterPlan(
        goal=AgentStarterGoal.CODING,
        requirements=[
            AgentStarterRequirement(
                key="paid_external_services_allowed",
                value=False,
                strength=ConstraintStrength.HARD,
                evidence=[
                    paid_external_evidence,
                ],
            ),
        ],
        candidate_assessments=[
            assessment,
        ],
    )

    hardware = HardwareProfile(
        device_class=DeviceClass.LAPTOP,
        source=HardwareProfileSource.NATIVE,
        total_memory_bytes=8 * 1024**3,
    )

    def local_entry(
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
                "capabilities": ["coding"],
                "deployment_modes": ["on_device"],
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
                "verified_at": "2026-08-29T00:00:00+00:00",
            }
        )

    paid_remote = AgentStarterCatalogEntry.model_validate(
        {
            "schema_version": "0.2",
            "identifier": "paid-remote-model",
            "component_type": "llm",
            "vendor": "Example Vendor",
            "family": "Example",
            "version": "1.0",
            "capabilities": ["coding"],
            "deployment_modes": ["remote"],
            "license": "example-license",
            "pricing_class": "free",
            "access_options": [
                {
                    "deployment_mode": "remote",
                    "access_kind": "external_service",
                    "pricing": "usage_based",
                },
            ],
            "sources": [
                "https://example.invalid/paid-remote-model",
            ],
            "verified_at": "2026-08-29T00:00:00+00:00",
        }
    )

    compatible = local_entry(
        "local-3b-q4",
        parameter_count=3_000_000_000,
        quantization="q4",
    )
    constrained = local_entry(
        "local-7b-q4",
        parameter_count=7_000_000_000,
        quantization="q4",
    )
    unknown = local_entry(
        "local-unknown",
    )
    not_recommended = local_entry(
        "local-30b-q4",
        parameter_count=30_000_000_000,
        quantization="q4",
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-hardware-composition-test",
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
            paid_remote,
        ],
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

    assert [
        entry.identifier
        for entry in query_match.matched_entries
    ] == [
        "local-3b-q4",
    ]

    assert [
        entry.identifier
        for entry in query_match.constrained_entries
    ] == [
        "local-7b-q4",
    ]

    assert [
        entry.identifier
        for entry in query_match.indeterminate_entries
    ] == [
        "local-unknown",
    ]

    assert [
        entry.identifier
        for entry in query_match.not_recommended_entries
    ] == [
        "local-30b-q4",
    ]

    assert [
        entry.identifier
        for entry in query_match.constraint_excluded_entries
    ] == [
        "paid-remote-model",
    ]
