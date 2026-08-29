from __future__ import annotations

from observer.core.agent_starter_catalog_matcher import (
    match_agent_starter_catalog_entries,
)
from observer.core.agent_starter_catalog_query_builder import (
    build_agent_starter_catalog_queries,
)
from observer.core.compatibility_estimator import (
    estimate_local_compatibility,
)
from schemas.agent_starter import (
    AgentStarterGoal,
    AgentStarterRequirement,
    CandidateArchitectureAssessment,
    ConstraintStrength,
)
from schemas.agent_starter_catalog import (
    AgentStarterCatalogAccessKind,
    AgentStarterCatalogAccessPricing,
    AgentStarterCatalogArchitectureResult,
    AgentStarterCatalogEntry,
    AgentStarterCatalogQuery,
    AgentStarterCatalogQueryMatch,
    AgentStarterCatalogSnapshot,
)
from schemas.compatibility import CompatibilityVerdict
from schemas.hardware import HardwareProfile


def _disallows_paid_external_services(
    plan_requirements: list[AgentStarterRequirement],
) -> bool:
    return any(
        requirement.key
        == "paid_external_services_allowed"
        and requirement.value is False
        and requirement.strength is ConstraintStrength.HARD
        for requirement in plan_requirements
    )


def _classify_external_service_cost_constraint(
    entries: list[AgentStarterCatalogEntry],
    *,
    query: AgentStarterCatalogQuery,
) -> tuple[
    list[AgentStarterCatalogEntry],
    list[AgentStarterCatalogEntry],
    list[AgentStarterCatalogEntry],
]:
    matched_entries: list[AgentStarterCatalogEntry] = []
    indeterminate_entries: list[AgentStarterCatalogEntry] = []
    constraint_excluded_entries: list[
        AgentStarterCatalogEntry
    ] = []

    indeterminate_pricing = {
        AgentStarterCatalogAccessPricing.FREEMIUM,
        AgentStarterCatalogAccessPricing.PROVIDER_DEPENDENT,
        AgentStarterCatalogAccessPricing.UNKNOWN,
    }
    paid_external_pricing = {
        AgentStarterCatalogAccessPricing.USAGE_BASED,
        AgentStarterCatalogAccessPricing.SUBSCRIPTION,
        AgentStarterCatalogAccessPricing.ENTERPRISE,
    }

    required_deployment_modes = set(
        query.required_deployment_modes
    )

    for entry in entries:
        if not entry.access_options:
            indeterminate_entries.append(entry)
            continue

        eligible_access_options = [
            option
            for option in entry.access_options
            if (
                not required_deployment_modes
                or option.deployment_mode
                in required_deployment_modes
            )
        ]

        if not eligible_access_options:
            indeterminate_entries.append(entry)
            continue

        has_compliant_path = False
        has_indeterminate_path = False

        for option in eligible_access_options:
            if (
                option.access_kind
                is AgentStarterCatalogAccessKind.SELF_HOSTED
            ):
                has_compliant_path = True
                break

            if (
                option.access_kind
                is AgentStarterCatalogAccessKind.EXTERNAL_SERVICE
            ):
                if (
                    option.pricing
                    is AgentStarterCatalogAccessPricing.FREE
                ):
                    has_compliant_path = True
                    break

                if option.pricing in indeterminate_pricing:
                    has_indeterminate_path = True
                    continue

                if option.pricing in paid_external_pricing:
                    continue

        if has_compliant_path:
            matched_entries.append(entry)
        elif has_indeterminate_path:
            indeterminate_entries.append(entry)
        else:
            constraint_excluded_entries.append(entry)

    return (
        matched_entries,
        indeterminate_entries,
        constraint_excluded_entries,
    )


def _classify_local_hardware_compatibility(
    entries: list[AgentStarterCatalogEntry],
    *,
    query: AgentStarterCatalogQuery,
    hardware: HardwareProfile,
) -> tuple[
    list[AgentStarterCatalogEntry],
    list[AgentStarterCatalogEntry],
    list[AgentStarterCatalogEntry],
    list[AgentStarterCatalogEntry],
]:
    matched_entries: list[AgentStarterCatalogEntry] = []
    constrained_entries: list[
        AgentStarterCatalogEntry
    ] = []
    indeterminate_entries: list[
        AgentStarterCatalogEntry
    ] = []
    not_recommended_entries: list[
        AgentStarterCatalogEntry
    ] = []

    required_deployment_modes = set(
        query.required_deployment_modes
    )

    for entry in entries:
        eligible_access_options = [
            option
            for option in entry.access_options
            if (
                not required_deployment_modes
                or option.deployment_mode
                in required_deployment_modes
            )
        ]

        if not eligible_access_options:
            indeterminate_entries.append(entry)
            continue

        has_compatible_path = False
        has_constrained_path = False
        has_unknown_path = False

        for option in eligible_access_options:
            if option.deployment_mode != "on_device":
                has_compatible_path = True
                break

            if option.model_profile is None:
                has_unknown_path = True
                continue

            assessment = estimate_local_compatibility(
                hardware,
                option.model_profile,
            )

            if (
                assessment.verdict
                is CompatibilityVerdict.COMPATIBLE
            ):
                has_compatible_path = True
                break

            if (
                assessment.verdict
                is CompatibilityVerdict.CONSTRAINED
            ):
                has_constrained_path = True
                continue

            if (
                assessment.verdict
                is CompatibilityVerdict.UNKNOWN
            ):
                has_unknown_path = True

        if has_compatible_path:
            matched_entries.append(entry)
        elif has_constrained_path:
            constrained_entries.append(entry)
        elif has_unknown_path:
            indeterminate_entries.append(entry)
        else:
            not_recommended_entries.append(entry)

    return (
        matched_entries,
        constrained_entries,
        indeterminate_entries,
        not_recommended_entries,
    )


def match_agent_starter_architecture_to_catalog(
    *,
    goal: AgentStarterGoal,
    assessment: CandidateArchitectureAssessment,
    snapshot: AgentStarterCatalogSnapshot,
    plan_requirements: list[
        AgentStarterRequirement
    ] | None = None,
    hardware_profile: HardwareProfile | None = None,
) -> AgentStarterCatalogArchitectureResult:
    queries = build_agent_starter_catalog_queries(
        goal=goal,
        assessment=assessment,
        plan_requirements=plan_requirements,
    )

    query_matches: list[AgentStarterCatalogQueryMatch] = []

    paid_external_services_disallowed = (
        _disallows_paid_external_services(
            list(plan_requirements or [])
        )
    )

    for query in queries:
        technical_matches = match_agent_starter_catalog_entries(
            snapshot=snapshot,
            query=query,
        )

        if paid_external_services_disallowed:
            (
                matched_entries,
                indeterminate_entries,
                constraint_excluded_entries,
            ) = _classify_external_service_cost_constraint(
                technical_matches,
                query=query,
            )
        else:
            matched_entries = technical_matches
            indeterminate_entries = []
            constraint_excluded_entries = []

        constrained_entries: list[
            AgentStarterCatalogEntry
        ] = []
        not_recommended_entries: list[
            AgentStarterCatalogEntry
        ] = []

        if hardware_profile is not None:
            (
                matched_entries,
                constrained_entries,
                hardware_indeterminate_entries,
                not_recommended_entries,
            ) = _classify_local_hardware_compatibility(
                matched_entries,
                query=query,
                hardware=hardware_profile,
            )

            indeterminate_entries = [
                *indeterminate_entries,
                *hardware_indeterminate_entries,
            ]

        query_matches.append(
            AgentStarterCatalogQueryMatch(
                architecture_id=assessment.architecture_id,
                catalog_snapshot_id=snapshot.snapshot_id,
                query=query,
                matched_entries=matched_entries,
                constrained_entries=constrained_entries,
                indeterminate_entries=indeterminate_entries,
                not_recommended_entries=(
                    not_recommended_entries
                ),
                constraint_excluded_entries=(
                    constraint_excluded_entries
                ),
            )
        )

    return AgentStarterCatalogArchitectureResult(
        architecture_id=assessment.architecture_id,
        catalog_snapshot_id=snapshot.snapshot_id,
        query_matches=query_matches,
    )


def match_agent_starter_candidates_to_catalog(
    *,
    goal: AgentStarterGoal,
    assessments: list[CandidateArchitectureAssessment],
    snapshot: AgentStarterCatalogSnapshot,
    plan_requirements: list[
        AgentStarterRequirement
    ] | None = None,
    hardware_profile: HardwareProfile | None = None,
) -> list[AgentStarterCatalogArchitectureResult]:
    return [
        match_agent_starter_architecture_to_catalog(
            goal=goal,
            assessment=assessment,
            snapshot=snapshot,
            plan_requirements=plan_requirements,
            hardware_profile=hardware_profile,
        )
        for assessment in assessments
    ]
