from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from observer.core.action_task_environment import (
    ActionTaskEnvironment,
)
from observer.core.agent_technical_report import (
    build_agent_technical_report,
)
from observer.core.agent_test_session_runner import (
    AgentTestSessionRunner,
)
from observer.core.benchmark_task_assessment import (
    BenchmarkTaskAssessmentRunner,
)
from observer.core.benchmark_task_runner import (
    BenchmarkTaskRunner,
)
from observer.core.default_task_evaluator_registry import (
    build_default_task_evaluator_registry,
)
from observer.core.suite_bank import (
    SuiteBank,
    SuiteBankError,
)
from observer.core.suite_registry import (
    SuiteRegistry,
    SuiteRegistryError,
)
from observer.core.task_bank import (
    TaskBank,
    TaskBankError,
)
from observer.sut.local_http import LocalHTTPSUTAdapter
from schemas.agent_lab import (
    AgentLabRunArtifact,
    AgentTechnicalReport,
    AgentTestSession,
)
from schemas.benchmark import BenchmarkHarnessProfile


class AgentLabProtocolRunnerError(Exception):
    """
    Raised when an Agent Lab protocol run cannot be completed
    because of an operational or configuration error.
    """


@dataclass(frozen=True)
class AgentLabProtocolRun:
    session: AgentTestSession
    report: AgentTechnicalReport

    def to_artifact(self) -> AgentLabRunArtifact:
        return AgentLabRunArtifact(
            session=self.session,
            technical_report=self.report,
        )


class AgentLabProtocolRunner:
    def __init__(
        self,
        *,
        observer_id: str,
        region_code: str,
        suite_root: Path = Path("benchmark/suites"),
        task_root: Path = Path("benchmark/tasks"),
    ) -> None:
        self.observer_id = observer_id
        self.region_code = region_code
        self.suite_root = suite_root
        self.task_root = task_root

    def run(
        self,
        *,
        base_url: str,
        generated_at_utc: datetime,
    ) -> AgentLabProtocolRun:
        try:
            adapter = LocalHTTPSUTAdapter(
                base_url,
            )

            registry = SuiteRegistry(
                suite_bank=SuiteBank(
                    self.suite_root,
                ),
                task_bank=TaskBank(
                    self.task_root,
                ),
            )

            resolved = registry.resolve_unique_for_target(
                adapter.manifest,
                harness_profile=(
                    BenchmarkHarnessProfile.SUT_PROTOCOL
                ),
            )

            task_runner = BenchmarkTaskRunner(
                adapter,
                observer_id=self.observer_id,
                region_code=self.region_code,
            )

            assessment_runner = BenchmarkTaskAssessmentRunner(
                task_runner=task_runner,
                registry=(
                    build_default_task_evaluator_registry()
                ),
            )

            session_runner = AgentTestSessionRunner(
                assessment_runner=assessment_runner,
            )

            with ExitStack() as stack:
                task_metadata = {}
                evidence_collectors = {}

                for task in resolved.tasks:
                    if (
                        task.expected_action is None
                        and task.expected_actions is None
                    ):
                        continue

                    environment = stack.enter_context(
                        ActionTaskEnvironment(task)
                    )

                    task_metadata[task.task_id] = (
                        environment.metadata
                    )
                    evidence_collectors[task.task_id] = (
                        environment.collector
                    )

                session = session_runner.run(
                    suite_id=resolved.suite.suite_id,
                    suite_version=resolved.suite.suite_version,
                    tasks=list(resolved.tasks),
                    task_metadata=task_metadata,
                    evidence_collectors=(
                        evidence_collectors
                    ),
                )

            report = build_agent_technical_report(
                session,
                generated_at_utc=generated_at_utc,
            )

            return AgentLabProtocolRun(
                session=session,
                report=report,
            )

        except (
            ValueError,
            OSError,
            KeyError,
            SuiteBankError,
            TaskBankError,
            SuiteRegistryError,
        ) as exc:
            raise AgentLabProtocolRunnerError(
                str(exc)
            ) from exc
