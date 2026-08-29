from datetime import datetime, timezone

from observer.core.agent_starter_catalog_orchestrator import (
    match_agent_starter_architecture_to_catalog,
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
    AgentStarterCatalogComponentType,
    AgentStarterCatalogEntry,
    AgentStarterCatalogSnapshot,
)


def _entry(
    *,
    identifier: str,
    capabilities: list[str],
) -> AgentStarterCatalogEntry:
    return AgentStarterCatalogEntry(
        identifier=identifier,
        component_type=AgentStarterCatalogComponentType.LLM,
        vendor="Example Vendor",
        family="Example",
        version="1.0",
        capabilities=capabilities,
        license="example-license",
        pricing_class="free",
        sources=[
            f"https://example.invalid/{identifier}",
        ],
        verified_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )


def test_catalog_orchestrator_matches_coding_architecture():
    first_match = _entry(
        identifier="coding-model-a",
        capabilities=["coding", "tool_use"],
    )
    non_match = _entry(
        identifier="general-model",
        capabilities=["general_chat"],
    )
    second_match = _entry(
        identifier="coding-model-b",
        capabilities=["coding"],
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
            first_match,
            non_match,
            second_match,
        ],
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
                key="source_code_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Source code remains inside the "
                    "user-controlled environment."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding-agent architecture requires "
                    "a language model."
                ),
            ),
        ],
    )

    result = match_agent_starter_architecture_to_catalog(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
        snapshot=snapshot,
    )

    assert result.architecture_id == "local-coding-agent"
    assert result.catalog_snapshot_id == "catalog-2026-08-28"
    assert len(result.query_matches) == 1

    query_match = result.query_matches[0]

    assert query_match.architecture_id == "local-coding-agent"
    assert (
        query_match.catalog_snapshot_id
        == "catalog-2026-08-28"
    )
    assert query_match.query.required_capabilities == ["coding"]
    assert [
        entry.identifier
        for entry in query_match.matched_entries
    ] == [
        "coding-model-a",
        "coding-model-b",
    ]


def test_catalog_orchestrator_preserves_deterministic_automation_without_queries():
    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[],
    )

    assessment = CandidateArchitectureAssessment(
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
                reason=(
                    "The deterministic automation architecture "
                    "does not use an LLM."
                ),
            ),
        ],
    )

    result = match_agent_starter_architecture_to_catalog(
        goal=AgentStarterGoal.AUTOMATION,
        assessment=assessment,
        snapshot=snapshot,
    )

    assert (
        result.architecture_id
        == "traditional-deterministic-automation"
    )
    assert result.catalog_snapshot_id == "catalog-2026-08-28"
    assert result.query_matches == []


def test_catalog_orchestrator_preserves_query_with_zero_matches():
    non_matching = _entry(
        identifier="general-model",
        capabilities=[
            "general_chat",
        ],
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
            non_matching,
        ],
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
                key="source_code_remote_processing",
                source=EvidenceSource.DERIVED,
                value=False,
                reason=(
                    "Source code remains inside the "
                    "user-controlled environment."
                ),
            ),
            AgentStarterEvidence(
                key="candidate_uses_llm",
                source=EvidenceSource.DERIVED,
                value=True,
                reason=(
                    "The coding-agent architecture requires "
                    "a language model."
                ),
            ),
        ],
    )

    result = match_agent_starter_architecture_to_catalog(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
        snapshot=snapshot,
    )

    assert len(result.query_matches) == 1

    query_match = result.query_matches[0]

    assert query_match.query.required_capabilities == [
        "coding",
    ]
    assert query_match.matched_entries == []


def test_catalog_orchestrator_preserves_all_candidate_assessments_in_order():
    llm = _entry(
        identifier="automation-model",
        capabilities=[],
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-2026-08-28",
        generated_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        entries=[llm],
    )

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

    from observer.core.agent_starter_catalog_orchestrator import (
        match_agent_starter_candidates_to_catalog,
    )

    results = match_agent_starter_candidates_to_catalog(
        goal=AgentStarterGoal.AUTOMATION,
        assessments=[
            deterministic,
            llm_automation,
        ],
        snapshot=snapshot,
    )

    assert [
        result.architecture_id
        for result in results
    ] == [
        "traditional-deterministic-automation",
        "supervised-automation-agent",
    ]

    assert results[0].query_matches == []

    assert len(results[1].query_matches) == 1
    assert [
        entry.identifier
        for entry in results[1].query_matches[0].matched_entries
    ] == [
        "automation-model",
    ]


def test_catalog_orchestrator_classifies_paid_external_service_constraint():
    from schemas.agent_starter import (
        AgentStarterRequirement,
        ConstraintStrength,
    )

    constraint_evidence = AgentStarterEvidence(
        key="paid_external_services_allowed",
        source=EvidenceSource.DECLARED,
        value=False,
    )

    paid_external_constraint = AgentStarterRequirement(
        key="paid_external_services_allowed",
        value=False,
        strength=ConstraintStrength.HARD,
        evidence=[
            constraint_evidence,
        ],
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

    def entry(
        identifier: str,
        *,
        access_options: list[dict] | None = None,
        schema_version: str = "0.2",
    ) -> AgentStarterCatalogEntry:
        options = list(access_options or [])

        deployment_modes = list(
            dict.fromkeys(
                option["deployment_mode"]
                for option in options
            )
        )

        return AgentStarterCatalogEntry.model_validate(
            {
                "schema_version": schema_version,
                "identifier": identifier,
                "component_type": "llm",
                "vendor": "Example Vendor",
                "family": "Example",
                "version": "1.0",
                "capabilities": [
                    "coding",
                ],
                "deployment_modes": deployment_modes,
                "license": "example-license",
                "pricing_class": "free",
                "access_options": options,
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

    self_hosted_subscription = entry(
        "self-hosted-subscription",
        access_options=[
            {
                "deployment_mode": "on_device",
                "access_kind": "self_hosted",
                "pricing": "subscription",
            },
        ],
    )

    external_free = entry(
        "external-free",
        access_options=[
            {
                "deployment_mode": "remote",
                "access_kind": "external_service",
                "pricing": "free",
            },
        ],
    )

    external_paid = entry(
        "external-paid",
        access_options=[
            {
                "deployment_mode": "remote",
                "access_kind": "external_service",
                "pricing": "usage_based",
            },
        ],
    )

    external_unknown = entry(
        "external-unknown",
        access_options=[
            {
                "deployment_mode": "remote",
                "access_kind": "external_service",
                "pricing": "provider_dependent",
            },
        ],
    )

    external_freemium = entry(
        "external-freemium",
        access_options=[
            {
                "deployment_mode": "remote",
                "access_kind": "external_service",
                "pricing": "freemium",
            },
        ],
    )

    mixed_access = entry(
        "mixed-access",
        access_options=[
            {
                "deployment_mode": "remote",
                "access_kind": "external_service",
                "pricing": "usage_based",
            },
            {
                "deployment_mode": "on_device",
                "access_kind": "self_hosted",
                "pricing": "free",
            },
        ],
    )

    legacy_entry = entry(
        "legacy-entry",
        schema_version="0.1",
    )

    snapshot = AgentStarterCatalogSnapshot(
        snapshot_id="catalog-v0-2-cost-test",
        generated_at=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ),
        entries=[
            self_hosted_subscription,
            external_free,
            external_paid,
            external_unknown,
            external_freemium,
            mixed_access,
            legacy_entry,
        ],
    )

    result = match_agent_starter_architecture_to_catalog(
        goal=AgentStarterGoal.CODING,
        assessment=assessment,
        snapshot=snapshot,
        plan_requirements=[
            paid_external_constraint,
        ],
    )

    query_match = result.query_matches[0]

    assert [
        item.identifier
        for item in query_match.matched_entries
    ] == [
        "self-hosted-subscription",
        "external-free",
        "mixed-access",
    ]

    assert [
        item.identifier
        for item in query_match.indeterminate_entries
    ] == [
        "external-unknown",
        "external-freemium",
        "legacy-entry",
    ]

    assert [
        item.identifier
        for item in query_match.constraint_excluded_entries
    ] == [
        "external-paid",
    ]


def test_external_service_cost_classification_respects_query_deployment_mode():
    from observer.core.agent_starter_catalog_orchestrator import (
        _classify_external_service_cost_constraint,
    )
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogEntry,
        AgentStarterCatalogQuery,
    )

    mixed = AgentStarterCatalogEntry.model_validate(
        {
            "schema_version": "0.2",
            "identifier": "mixed-access-model",
            "component_type": "llm",
            "vendor": "Example Vendor",
            "family": "Example",
            "version": "1.0",
            "capabilities": ["coding"],
            "deployment_modes": [
                "on_device",
                "remote",
            ],
            "license": "example-license",
            "pricing_class": "free",
            "access_options": [
                {
                    "deployment_mode": "on_device",
                    "access_kind": "self_hosted",
                    "pricing": "free",
                },
                {
                    "deployment_mode": "remote",
                    "access_kind": "external_service",
                    "pricing": "usage_based",
                },
            ],
            "sources": [
                "https://example.invalid/mixed-access-model",
            ],
            "verified_at": "2026-08-29T00:00:00+00:00",
        }
    )

    remote_query = AgentStarterCatalogQuery(
        component_type="llm",
        required_capabilities=["coding"],
        required_deployment_modes=["remote"],
    )

    (
        matched,
        indeterminate,
        excluded,
    ) = _classify_external_service_cost_constraint(
        [mixed],
        query=remote_query,
    )

    assert matched == []
    assert indeterminate == []
    assert excluded == [mixed]

    local_query = AgentStarterCatalogQuery(
        component_type="llm",
        required_capabilities=["coding"],
        required_deployment_modes=["on_device"],
    )

    (
        matched,
        indeterminate,
        excluded,
    ) = _classify_external_service_cost_constraint(
        [mixed],
        query=local_query,
    )

    assert matched == [mixed]
    assert indeterminate == []
    assert excluded == []

    unrestricted_query = AgentStarterCatalogQuery(
        component_type="llm",
        required_capabilities=["coding"],
    )

    (
        matched,
        indeterminate,
        excluded,
    ) = _classify_external_service_cost_constraint(
        [mixed],
        query=unrestricted_query,
    )

    assert matched == [mixed]
    assert indeterminate == []
    assert excluded == []


def test_external_service_cost_missing_required_path_is_indeterminate():
    from observer.core.agent_starter_catalog_orchestrator import (
        _classify_external_service_cost_constraint,
    )
    from schemas.agent_starter_catalog import (
        AgentStarterCatalogEntry,
        AgentStarterCatalogQuery,
    )

    entry = AgentStarterCatalogEntry.model_validate(
        {
            "schema_version": "0.2",
            "identifier": "incomplete-access-metadata",
            "component_type": "llm",
            "vendor": "Example Vendor",
            "family": "Example",
            "version": "1.0",
            "capabilities": ["coding"],
            "deployment_modes": [
                "on_device",
                "remote",
            ],
            "license": "example-license",
            "pricing_class": "free",
            "access_options": [
                {
                    "deployment_mode": "on_device",
                    "access_kind": "self_hosted",
                    "pricing": "free",
                },
            ],
            "sources": [
                "https://example.invalid/incomplete-access-metadata",
            ],
            "verified_at": "2026-08-29T00:00:00+00:00",
        }
    )

    query = AgentStarterCatalogQuery(
        component_type="llm",
        required_capabilities=["coding"],
        required_deployment_modes=["remote"],
    )

    (
        matched,
        indeterminate,
        excluded,
    ) = _classify_external_service_cost_constraint(
        [entry],
        query=query,
    )

    assert matched == []
    assert indeterminate == [entry]
    assert excluded == []
