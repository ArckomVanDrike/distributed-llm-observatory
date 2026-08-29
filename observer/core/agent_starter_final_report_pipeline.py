from __future__ import annotations

from observer.core.agent_starter_final_report_builder import (
    build_agent_starter_final_report,
)
from schemas.agent_starter import AgentStarterPreparedInput
from schemas.agent_starter_catalog import (
    AgentStarterCatalogSnapshot,
)
from schemas.agent_starter_report import (
    AgentStarterFinalReport,
    AgentStarterFinalReportContext,
)
from schemas.agent_starter_result import (
    AgentStarterConcreteStackClassification,
)


def run_agent_starter_final_report_pipeline(
    *,
    prepared: AgentStarterPreparedInput,
    classification: AgentStarterConcreteStackClassification,
    catalog_snapshot: AgentStarterCatalogSnapshot,
) -> AgentStarterFinalReport:
    context = AgentStarterFinalReportContext(
        prepared=prepared,
        classification=classification,
        catalog_snapshot=catalog_snapshot,
    )

    return build_agent_starter_final_report(
        context
    )
