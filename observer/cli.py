from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from consumer_probe.analytics import (
    summarize,
    summarize_first_output_by_mode,
    summarize_schedule_adherence,
)
from consumer_probe.bridge import BridgeConfig, serve
from consumer_probe.comparison import ComparisonPolicy
from consumer_probe.detection import detect_utc_bucket
from consumer_probe.due import (
    find_due_probe,
    find_next_probe,
)
from consumer_probe.importer import (
    ConsumerProbeImportError,
    import_export,
)
from consumer_probe.sampling import SamplingPolicy
from consumer_probe.schemas import ConsumerPlatform
from consumer_probe.storage.sqlite import (
    ConsumerProbeSQLiteStore,
    ConsumerProbeStoreError,
)
from consumer_probe.telemetry_analytics import (
    summarize_local_telemetry_by_collector,
    summarize_local_telemetry_records,
)
from observer.core.agent_lab_artifact_io import (
    AgentLabArtifactIOError,
    load_agent_lab_run_artifact,
    write_agent_lab_run_artifact,
)
from observer.core.agent_lab_geographic_comparison import (
    compare_geographic_agent_observations,
)
from observer.core.agent_lab_observation_pairs import (
    discover_geographic_agent_observation_pairs,
    discover_temporal_agent_observation_pairs,
)
from observer.core.agent_lab_observation_qualification import (
    qualify_agent_observation,
)
from observer.core.agent_lab_protocol_runner import (
    AgentLabProtocolRunner,
    AgentLabProtocolRunnerError,
)
from observer.core.agent_lab_run_comparison import (
    compare_agent_lab_runs,
)
from observer.core.agent_lab_run_history import (
    AgentLabRunHistory,
)
from observer.core.agent_lab_temporal_comparison import (
    compare_temporal_agent_observations,
)
from observer.core.benchmark_runner import BenchmarkRunner
from observer.core.config import ObserverConfig, ObserverConfigError
from observer.core.consumer_schedule import (
    ConsumerScheduleError,
    build_prompt_bank_schedule,
)
from observer.core.prompt_bank import PromptBank, PromptBankError
from observer.core.recording import build_observation_record
from observer.core.task_bank import TaskBank, TaskBankError
from observer.providers.mock import MockProvider
from observer.storage.sqlite import SQLiteObservationStore

DEFAULT_CONSUMER_STORAGE = Path(
    "data/consumer-probes.db"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dllo",
        description="Distributed LLM Observatory observer node",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # -----------------------------------------------------
    # API benchmark runner
    # -----------------------------------------------------

    run_parser = subparsers.add_parser(
        "run",
        help="Run one benchmark prompt",
    )

    run_parser.add_argument(
        "--benchmark",
        required=True,
        help="Benchmark prompt ID, for example reasoning-001",
    )

    run_parser.add_argument(
        "--provider",
        default="mock",
        choices=["mock"],
        help="Provider adapter to use",
    )

    run_parser.add_argument(
        "--model",
        default="mock-model",
        help="Provider model identifier",
    )

    run_parser.add_argument(
        "--prompt-bank",
        type=Path,
        default=Path("benchmark/prompts"),
        help="Benchmark prompt bank directory",
    )

    # -----------------------------------------------------
    # Consumer Probe import
    # -----------------------------------------------------

    import_parser = subparsers.add_parser(
        "consumer-import",
        help="Import a Consumer Probe browser export",
    )

    import_parser.add_argument(
        "export",
        type=Path,
        help="Path to Consumer Probe JSON export",
    )

    import_parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_CONSUMER_STORAGE,
        help="Consumer Probe SQLite database",
    )

    import_parser.add_argument(
        "--observer-id",
        help=(
            "Observer identifier. Defaults to "
            "OBSERVATORY_ID when omitted."
        ),
    )

    import_parser.add_argument(
        "--region-code",
        help=(
            "Observer region. Defaults to "
            "OBSERVATORY_REGION when omitted."
        ),
    )

    import_parser.add_argument(
        "--observer-timezone",
        help=(
            "IANA observer timezone, for example "
            "America/Santiago"
        ),
    )

    # -----------------------------------------------------
    # Consumer Probe summary
    # -----------------------------------------------------

    summary_parser = subparsers.add_parser(
        "consumer-summary",
        help="Summarize stored Consumer Probe observations",
    )

    summary_parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_CONSUMER_STORAGE,
        help="Consumer Probe SQLite database",
    )

    # -----------------------------------------------------
    # Consumer Probe anomaly detection
    # -----------------------------------------------------

    detect_parser = subparsers.add_parser(
        "consumer-detect",
        help=(
            "Compare one UTC bucket against its "
            "historical baseline"
        ),
    )

    detect_parser.add_argument(
        "--candidate-start",
        required=True,
        help=(
            "UTC bucket start in ISO 8601 format, for "
            "example 2026-08-19T20:00:00Z"
        ),
    )

    detect_parser.add_argument(
        "--platform",
        required=True,
        choices=[
            platform.value
            for platform in ConsumerPlatform
        ],
        help="Consumer platform",
    )

    detect_parser.add_argument(
        "--region-code",
        required=True,
        help="Observer region code",
    )

    detect_parser.add_argument(
        "--benchmark-version",
        default="0.1",
        help="Benchmark version",
    )

    detect_parser.add_argument(
        "--prompt-id",
        required=True,
        help="Benchmark prompt ID",
    )

    detect_parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_CONSUMER_STORAGE,
        help="Consumer Probe SQLite database",
    )

    detect_parser.add_argument(
        "--lookback-days",
        type=int,
        default=14,
        help="Historical baseline lookback window",
    )

    detect_parser.add_argument(
        "--bucket-hours",
        type=int,
        default=4,
        help="UTC bucket size",
    )

    detect_parser.add_argument(
        "--min-samples",
        type=int,
        default=20,
        help="Minimum candidate and baseline sample count",
    )

    # -----------------------------------------------------
    # Consumer Probe daily schedule
    # -----------------------------------------------------

    schedule_parser = subparsers.add_parser(
        "consumer-schedule",
        help="Build the daily Consumer Probe benchmark schedule",
    )

    schedule_parser.add_argument(
        "--date",
        dest="sampling_date",
        help=(
            "UTC sampling date in YYYY-MM-DD format. "
            "Defaults to the current UTC date."
        ),
    )

    schedule_parser.add_argument(
        "--observer-id",
        help=(
            "Observer identifier. Defaults to "
            "OBSERVATORY_ID when omitted."
        ),
    )

    schedule_parser.add_argument(
        "--benchmark-version",
        default="0.1",
        help="Benchmark version",
    )

    schedule_parser.add_argument(
        "--prompt-bank",
        type=Path,
        default=Path("benchmark/prompts"),
        help="Benchmark prompt bank directory",
    )

    schedule_parser.add_argument(
        "--bucket-hours",
        type=int,
        default=4,
        help="UTC sampling bucket size",
    )

    schedule_parser.add_argument(
        "--samples-per-bucket",
        type=int,
        default=1,
        help="Sampling slots per UTC bucket",
    )

    schedule_parser.add_argument(
        "--edge-guard-minutes",
        type=int,
        default=15,
        help="Minutes excluded from each bucket edge",
    )

    # -----------------------------------------------------
    # Consumer Probe due / next selector
    # -----------------------------------------------------

    next_parser = subparsers.add_parser(
        "consumer-next",
        help="Show the due or next Consumer Probe benchmark",
    )

    next_parser.add_argument(
        "--platform",
        required=True,
        choices=[
            platform.value
            for platform in ConsumerPlatform
        ],
        help="Consumer platform",
    )

    next_parser.add_argument(
        "--observer-id",
        help=(
            "Observer identifier. Defaults to "
            "OBSERVATORY_ID when omitted."
        ),
    )

    next_parser.add_argument(
        "--date",
        dest="sampling_date",
        help=(
            "Schedule date in YYYY-MM-DD format. "
            "Defaults to the UTC date of --now."
        ),
    )

    next_parser.add_argument(
        "--now",
        dest="now_utc",
        help=(
            "Current UTC time override in ISO 8601 format. "
            "Defaults to the real current UTC time."
        ),
    )

    next_parser.add_argument(
        "--benchmark-version",
        default="0.1",
        help="Benchmark version",
    )

    next_parser.add_argument(
        "--prompt-bank",
        type=Path,
        default=Path("benchmark/prompts"),
        help="Benchmark prompt bank directory",
    )

    next_parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_CONSUMER_STORAGE,
        help="Consumer Probe SQLite database",
    )

    next_parser.add_argument(
        "--bucket-hours",
        type=int,
        default=4,
        help="UTC sampling bucket size",
    )

    next_parser.add_argument(
        "--samples-per-bucket",
        type=int,
        default=1,
        help="Sampling slots per UTC bucket",
    )

    next_parser.add_argument(
        "--edge-guard-minutes",
        type=int,
        default=15,
        help="Minutes excluded from each bucket edge",
    )

    next_parser.add_argument(
        "--grace-minutes",
        type=int,
        default=60,
        help="Minutes after scheduled time that a probe remains due",
    )

    next_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output",
    )

    # -----------------------------------------------------
    # Consumer Probe localhost bridge
    # -----------------------------------------------------

    bridge_parser = subparsers.add_parser(
        "consumer-bridge",
        help="Run the localhost Consumer Probe HTTP bridge",
    )

    bridge_parser.add_argument(
        "--platform",
        required=True,
        choices=[
            platform.value
            for platform in ConsumerPlatform
        ],
        help="Consumer platform",
    )

    bridge_parser.add_argument(
        "--observer-id",
        help=(
            "Observer identifier. Defaults to "
            "OBSERVATORY_ID when omitted."
        ),
    )

    bridge_parser.add_argument(
        "--benchmark-version",
        default="0.1",
        help="Benchmark version",
    )

    bridge_parser.add_argument(
        "--prompt-bank",
        type=Path,
        default=Path("benchmark/prompts"),
        help="Benchmark prompt bank directory",
    )

    bridge_parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_CONSUMER_STORAGE,
        help="Consumer Probe SQLite database",
    )

    bridge_parser.add_argument(
        "--bucket-hours",
        type=int,
        default=4,
        help="UTC sampling bucket size",
    )

    bridge_parser.add_argument(
        "--samples-per-bucket",
        type=int,
        default=1,
        help="Sampling slots per UTC bucket",
    )

    bridge_parser.add_argument(
        "--edge-guard-minutes",
        type=int,
        default=15,
        help="Minutes excluded from each bucket edge",
    )

    bridge_parser.add_argument(
        "--grace-minutes",
        type=int,
        default=60,
        help="Minutes after scheduled time that a probe remains due",
    )

    bridge_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bridge bind host; localhost only",
    )

    bridge_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Bridge TCP port",
    )

    bridge_parser.add_argument(
        "--collector-static-root",
        type=Path,
        default=None,
        help=(
            "Optional local Collector build directory "
            "to serve from the bridge"
        ),
    )

    # -----------------------------------------------------
    # Agent Lab protocol test
    # -----------------------------------------------------

    agent_test_parser = subparsers.add_parser(
        "agent-test",
        help="Test an agent through the Local SUT Protocol",
    )

    agent_test_parser.add_argument(
        "base_url",
        help=(
            "Local SUT Protocol base URL, for example "
            "http://127.0.0.1:8000"
        ),
    )

    agent_test_parser.add_argument(
        "--observer-id",
        help=(
            "Observer identifier. Defaults to "
            "OBSERVATORY_ID when omitted."
        ),
    )

    agent_test_parser.add_argument(
        "--region-code",
        help=(
            "Observer region. Defaults to "
            "OBSERVATORY_REGION when omitted."
        ),
    )

    agent_test_parser.add_argument(
        "--suite-bank",
        type=Path,
        default=Path("benchmark/suites"),
        help="Benchmark suite bank directory",
    )

    agent_test_parser.add_argument(
        "--task-bank",
        type=Path,
        default=Path("benchmark/tasks"),
        help="Benchmark task bank directory",
    )

    agent_test_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optional path for the Agent Lab run "
            "artifact JSON"
        ),
    )

    # -----------------------------------------------------
    # Agent Lab run comparison
    # -----------------------------------------------------

    agent_compare_parser = subparsers.add_parser(
        "agent-compare",
        help="Compare two Agent Lab run artifacts",
    )

    agent_compare_parser.add_argument(
        "baseline",
        type=Path,
        help="Baseline Agent Lab run artifact JSON",
    )

    agent_compare_parser.add_argument(
        "candidate",
        type=Path,
        help="Candidate Agent Lab run artifact JSON",
    )

    # -----------------------------------------------------
    # Agent Lab temporal comparison
    # -----------------------------------------------------

    agent_compare_temporal_parser = subparsers.add_parser(
        "agent-compare-temporal",
        help=(
            "Compare two Agent Lab observations "
            "across time"
        ),
    )

    agent_compare_temporal_parser.add_argument(
        "baseline",
        type=Path,
        help="Baseline Agent Lab run artifact JSON",
    )

    agent_compare_temporal_parser.add_argument(
        "candidate",
        type=Path,
        help="Candidate Agent Lab run artifact JSON",
    )

    # -----------------------------------------------------
    # Agent Lab geographic comparison
    # -----------------------------------------------------

    agent_compare_geographic_parser = subparsers.add_parser(
        "agent-compare-geographic",
        help=(
            "Compare two Agent Lab observations "
            "across regions"
        ),
    )

    agent_compare_geographic_parser.add_argument(
        "baseline",
        type=Path,
        help="Baseline Agent Lab run artifact JSON",
    )

    agent_compare_geographic_parser.add_argument(
        "candidate",
        type=Path,
        help="Candidate Agent Lab run artifact JSON",
    )

    agent_compare_geographic_parser.add_argument(
        "--max-observation-skew-seconds",
        type=float,
        required=True,
        help=(
            "Maximum allowed observation time skew "
            "in seconds"
        ),
    )

    # -----------------------------------------------------
    # Agent Lab run history
    # -----------------------------------------------------

    agent_history_parser = subparsers.add_parser(
        "agent-history",
        help="List persisted Agent Lab run artifacts",
    )

    agent_history_parser.add_argument(
        "history_root",
        type=Path,
        help="Directory containing Agent Lab run artifacts",
    )

    agent_history_parser.add_argument(
        "--target",
        default=None,
        help="Optional target ID filter",
    )

    # -----------------------------------------------------
    # Agent Lab temporal pair discovery
    # -----------------------------------------------------

    agent_pairs_temporal_parser = subparsers.add_parser(
        "agent-pairs-temporal",
        help=(
            "Discover comparable Agent Lab observation "
            "pairs across time"
        ),
    )

    agent_pairs_temporal_parser.add_argument(
        "history_root",
        type=Path,
        help="Directory containing Agent Lab run artifacts",
    )

    agent_pairs_temporal_parser.add_argument(
        "--target",
        default=None,
        help="Optional target ID filter",
    )

    # -----------------------------------------------------
    # Agent Lab geographic pair discovery
    # -----------------------------------------------------

    agent_pairs_geographic_parser = subparsers.add_parser(
        "agent-pairs-geographic",
        help=(
            "Discover comparable Agent Lab observation "
            "pairs across regions"
        ),
    )

    agent_pairs_geographic_parser.add_argument(
        "history_root",
        type=Path,
        help="Directory containing Agent Lab run artifacts",
    )

    agent_pairs_geographic_parser.add_argument(
        "--target",
        default=None,
        help="Optional target ID filter",
    )

    agent_pairs_geographic_parser.add_argument(
        "--max-observation-skew-seconds",
        type=float,
        required=True,
        help=(
            "Maximum allowed observation time skew "
            "in seconds"
        ),
    )

    # -----------------------------------------------------
    # Benchmark task discovery
    # -----------------------------------------------------

    task_list_parser = subparsers.add_parser(
        "task-list",
        help="List enabled benchmark tasks",
    )

    task_list_parser.add_argument(
        "--task-bank",
        type=Path,
        default=Path("benchmark/tasks"),
        help="Benchmark task bank directory",
    )

    task_show_parser = subparsers.add_parser(
        "task-show",
        help="Show one benchmark task",
    )

    task_show_parser.add_argument(
        "task_id",
        help="Benchmark task ID",
    )

    task_show_parser.add_argument(
        "--task-bank",
        type=Path,
        default=Path("benchmark/tasks"),
        help="Benchmark task bank directory",
    )

    return parser


def run_benchmark(args: argparse.Namespace) -> int:
    try:
        config = ObserverConfig.from_environment()

        prompt_bank = PromptBank(args.prompt_bank)
        prompts = prompt_bank.load_enabled()

        benchmark = next(
            (
                prompt
                for prompt in prompts
                if prompt.prompt_id == args.benchmark
            ),
            None,
        )

        if benchmark is None:
            print(
                f"Benchmark not found: {args.benchmark}",
                file=sys.stderr,
            )
            return 2

        if args.provider == "mock":
            provider = MockProvider()
        else:
            print(
                f"Unsupported provider: {args.provider}",
                file=sys.stderr,
            )
            return 2

        runner = BenchmarkRunner(
            provider=provider,
            observer_id=config.observer_id,
            region_code=config.region_code,
            model=args.model,
        )

        run = runner.run(benchmark)
        record = build_observation_record(run)

        store = SQLiteObservationStore(
            config.storage_path
        )

        store.append(record)

        print(
            f"Observation ID: {record.observation_id}"
        )
        print(
            f"Prompt:         {benchmark.prompt_id}"
        )
        print(
            f"Provider:       {record.execution.provider}"
        )
        print(
            f"Model:          {record.execution.model}"
        )
        print(
            f"Region:         "
            f"{record.observer.region_code}"
        )
        print(
            f"Latency:        "
            f"{record.execution.latency_ms:.2f} ms"
        )
        print(
            f"Tokens/s:       "
            f"{record.execution.tokens_per_second:.2f}"
        )
        print(
            f"Storage:        {config.storage_path}"
        )

        return 0

    except (
        ObserverConfigError,
        PromptBankError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def resolve_observer_identity(
    args: argparse.Namespace,
) -> tuple[str, str]:
    observer_id = args.observer_id
    region_code = args.region_code

    if observer_id and region_code:
        return observer_id, region_code

    config = ObserverConfig.from_environment()

    return (
        observer_id or config.observer_id,
        region_code or config.region_code,
    )


def consumer_import(
    args: argparse.Namespace,
) -> int:
    try:
        observer_id, region_code = (
            resolve_observer_identity(args)
        )

        records = import_export(
            args.export,
            observer_id=observer_id,
            region_code=region_code,
            observer_timezone=args.observer_timezone,
        )

        store = ConsumerProbeSQLiteStore(
            args.storage
        )

        inserted, duplicates = store.append_many(
            records
        )

        print("Consumer Probe import complete")
        print(f"Validated:  {len(records)}")
        print(f"Inserted:   {inserted}")
        print(f"Duplicates: {duplicates}")
        print(f"DB total:   {store.count()}")
        print(f"Storage:    {args.storage}")

        return 0

    except (
        ConsumerProbeImportError,
        ConsumerProbeStoreError,
        ObserverConfigError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def format_ms(
    value: float | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:.2f} ms"


def format_rate(
    value: float | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:.2%}"


def format_percent(
    value: float | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:.2f}%"


def format_bytes(
    value: float | int | None,
) -> str:
    if value is None:
        return "n/a"

    mib = float(value) / 1024 / 1024

    if mib >= 1024:
        return f"{mib / 1024:.2f} GiB"

    return f"{mib:.2f} MiB"


def format_hz(
    value: float | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:.2f} Hz"


def consumer_summary(
    args: argparse.Namespace,
) -> int:
    try:
        store = ConsumerProbeSQLiteStore(
            args.storage
        )

        records = store.load_all()
        stats = summarize(records)
        first_output_by_mode = (
            summarize_first_output_by_mode(
                records
            )
        )
        adherence = summarize_schedule_adherence(
            records
        )
        host_telemetry = (
            summarize_local_telemetry_records(
                records
            )
        )
        telemetry_by_collector = (
            summarize_local_telemetry_by_collector(
                records
            )
        )

        print("=== DLLO CONSUMER SUMMARY ===")
        print(
            f"Samples:          "
            f"{stats.sample_count}"
        )
        print(
            f"Successful:       "
            f"{stats.successful_samples}"
        )
        print()
        print("=== FIRST OUTPUT BY MEASUREMENT MODE ===")

        if not first_output_by_mode:
            print("No first-output measurements.")
        else:
            for measurement_mode in sorted(
                first_output_by_mode,
                key=lambda mode: (
                    mode is not None,
                    mode or "",
                ),
            ):
                first_output = first_output_by_mode[
                    measurement_mode
                ]

                mode_label = (
                    measurement_mode
                    if measurement_mode is not None
                    else "legacy/unknown"
                )

                print(
                    f"--- MODE: {mode_label} ---"
                )
                print(
                    f"Samples:          "
                    f"{first_output.sample_count}"
                )
                print(
                    f"Median:           "
                    f"{format_ms(first_output.median_first_output_ms)}"
                )
                print(
                    f"P95:              "
                    f"{format_ms(first_output.p95_first_output_ms)}"
                )

        print()
        print("=== GENERAL PERFORMANCE ===")
        print(
            f"Median latency:   "
            f"{format_ms(stats.median_latency_ms)}"
        )
        print(
            f"P95 latency:      "
            f"{format_ms(stats.p95_latency_ms)}"
        )
        print(
            f"Failure rate:     "
            f"{stats.failure_rate:.2%}"
        )
        print(
            f"Retry rate:       "
            f"{stats.retry_rate:.2%}"
        )
        print(
            f"Interrupted rate: "
            f"{stats.interruption_rate:.2%}"
        )

        print()
        print("=== SCHEDULE ADHERENCE ===")
        print(
            f"Scheduled:        "
            f"{adherence.scheduled_samples}"
        )
        print(
            f"Unscheduled:      "
            f"{adherence.unscheduled_samples}"
        )
        print(
            f"Median offset:    "
            f"{format_ms(adherence.median_offset_ms)}"
        )
        print(
            f"P95 offset:       "
            f"{format_ms(adherence.p95_offset_ms)}"
        )
        print(
            f"Median abs offset:"
            f" "
            f"{format_ms(adherence.median_absolute_offset_ms)}"
        )
        print(
            f"P95 abs offset:   "
            f"{format_ms(adherence.p95_absolute_offset_ms)}"
        )
        print(
            f"Within +/-5 min:  "
            f"{format_rate(adherence.within_tolerance_rate)}"
        )

        print()
        print("=== LOCAL HOST TELEMETRY ===")
        print(
            f"Instrumented:     "
            f"{host_telemetry.telemetry_records}"
        )
        print(
            f"Telemetry errors: "
            f"{host_telemetry.telemetry_error_records}"
        )
        print(
            f"Uninstrumented:   "
            f"{host_telemetry.uninstrumented_records}"
        )
        print(
            f"Collectors:       "
            f"{len(telemetry_by_collector)}"
        )

        collector_versions = sorted(
            telemetry_by_collector,
            key=lambda value: (
                value is None,
                value or "",
            ),
        )

        for collector_version in collector_versions:
            collector = telemetry_by_collector[
                collector_version
            ]

            label = (
                collector_version
                if collector_version is not None
                else "legacy/unknown"
            )

            print()
            print(
                f"--- COLLECTOR: {label} ---"
            )
            print(
                f"Samples:          "
                f"{collector.telemetry_records}"
            )
            print(
                f"PSS records:      "
                f"{collector.pss_records}"
            )
            print(
                f"Median peak RSS:  "
                f"{format_bytes(collector.median_peak_browser_rss_bytes)}"
            )
            print(
                f"P95 peak RSS:     "
                f"{format_bytes(collector.p95_peak_browser_rss_bytes)}"
            )
            print(
                f"Median peak PSS:  "
                f"{format_bytes(collector.median_peak_browser_pss_bytes)}"
            )
            print(
                f"P95 peak PSS:     "
                f"{format_bytes(collector.p95_peak_browser_pss_bytes)}"
            )
            print(
                f"Median peak CPU:  "
                f"{format_percent(collector.median_peak_browser_cpu_percent)}"
            )
            print(
                f"P95 peak CPU:     "
                f"{format_percent(collector.p95_peak_browser_cpu_percent)}"
            )
            print(
                f"Fast sampling:    "
                f"{format_hz(collector.median_fast_sampling_hz)}"
            )
            print(
                f"PSS sampling:     "
                f"{format_hz(collector.median_pss_sampling_hz)}"
            )

            min_system_ram = format_bytes(
                collector.minimum_system_memory_available_bytes
            )

            print(
                f"Min system RAM:   "
                f"{min_system_ram}"
            )

        return 0

    except ConsumerProbeStoreError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def parse_candidate_start(
    raw_value: str,
) -> datetime:
    normalized = raw_value.strip()

    if normalized.endswith("Z"):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    try:
        value = datetime.fromisoformat(
            normalized
        )
    except ValueError as exc:
        raise ValueError(
            "candidate-start must be a valid "
            "ISO 8601 datetime."
        ) from exc

    if value.tzinfo is None:
        raise ValueError(
            "candidate-start must include UTC timezone."
        )

    if value.utcoffset() != timedelta(0):
        raise ValueError(
            "candidate-start must be expressed in UTC."
        )

    return value.astimezone(timezone.utc)


def consumer_detect(
    args: argparse.Namespace,
) -> int:
    try:
        candidate_start = parse_candidate_start(
            args.candidate_start
        )

        platform = ConsumerPlatform(
            args.platform
        )

        store = ConsumerProbeSQLiteStore(
            args.storage
        )

        policy = ComparisonPolicy(
            min_samples_per_group=args.min_samples
        )

        result = detect_utc_bucket(
            store.load_all(),
            candidate_start_utc=candidate_start,
            platform=platform,
            region_code=args.region_code,
            benchmark_version=args.benchmark_version,
            prompt_id=args.prompt_id,
            lookback_days=args.lookback_days,
            bucket_hours=args.bucket_hours,
            policy=policy,
        )

        comparison = result.comparison

        print("=== DLLO CONSUMER DETECTION ===")
        print(
            f"Platform:          "
            f"{args.platform}"
        )
        print(
            f"Region:            "
            f"{args.region_code}"
        )
        print(
            f"Prompt:            "
            f"{args.prompt_id}"
        )
        print(
            f"Candidate bucket:  "
            f"{result.candidate.bucket_label}"
        )
        print(
            f"Candidate samples: "
            f"{comparison.candidate_samples}"
        )
        print(
            f"Baseline samples:  "
            f"{comparison.baseline_samples}"
        )
        print(
            f"Level:             "
            f"{comparison.level.value}"
        )

        if comparison.ttfo_ratio is not None:
            print(
                f"First-output measurement mode: "
                f"{comparison.first_output_measurement_mode}"
            )
            print(
                f"First-output ratio: "
                f"{comparison.ttfo_ratio:.2f}x"
            )

        if comparison.latency_ratio is not None:
            print(
                f"Latency ratio:     "
                f"{comparison.latency_ratio:.2f}x"
            )

        print(
            f"Failure delta:     "
            f"{comparison.failure_rate_delta:.2%}"
        )
        print(
            f"Retry delta:       "
            f"{comparison.retry_rate_delta:.2%}"
        )
        print(
            f"Reason:            "
            f"{comparison.reason}"
        )

        return 0

    except (
        ConsumerProbeStoreError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def parse_sampling_date(
    raw_value: str | None,
) -> date:
    if raw_value is None:
        return datetime.now(
            timezone.utc
        ).date()

    try:
        return date.fromisoformat(
            raw_value.strip()
        )
    except ValueError as exc:
        raise ValueError(
            "date must use YYYY-MM-DD format."
        ) from exc


def consumer_schedule(
    args: argparse.Namespace,
) -> int:
    try:
        sampling_date = parse_sampling_date(
            args.sampling_date
        )

        observer_id = args.observer_id

        if not observer_id:
            config = ObserverConfig.from_environment()
            observer_id = config.observer_id

        policy = SamplingPolicy(
            bucket_hours=args.bucket_hours,
            samples_per_bucket=args.samples_per_bucket,
            edge_guard_minutes=args.edge_guard_minutes,
        )

        schedule = build_prompt_bank_schedule(
            sampling_date,
            observer_id=observer_id,
            benchmark_version=args.benchmark_version,
            prompt_bank_path=args.prompt_bank,
            sampling_policy=policy,
        )

        print("=== DLLO DAILY CONSUMER SCHEDULE ===")
        print(
            f"Date:              "
            f"{schedule.sampling_date}"
        )
        print(
            f"Observer:          "
            f"{schedule.observer_id}"
        )
        print(
            f"Benchmark version: "
            f"{schedule.benchmark_version}"
        )
        print(
            f"Scheduled items:   "
            f"{len(schedule.items)}"
        )

        for item in schedule.items:
            print(
                f"{item.scheduled_at_utc.isoformat()} "
                f"-> {item.benchmark.prompt_id} "
                f"[{item.benchmark.category.value}]"
            )

        return 0

    except (
        ConsumerScheduleError,
        ObserverConfigError,
        PromptBankError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def parse_now_utc(
    raw_value: str | None,
) -> datetime:
    if raw_value is None:
        return datetime.now(timezone.utc)

    normalized = raw_value.strip()

    if normalized.endswith("Z"):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    try:
        value = datetime.fromisoformat(
            normalized
        )
    except ValueError as exc:
        raise ValueError(
            "now must be a valid ISO 8601 datetime."
        ) from exc

    if value.tzinfo is None:
        raise ValueError(
            "now must include a UTC timezone."
        )

    if value.utcoffset() != timedelta(0):
        raise ValueError(
            "now must be expressed in UTC."
        )

    return value.astimezone(timezone.utc)


def completed_prompt_ids_for_day(
    records,
    *,
    observer_id: str,
    platform: ConsumerPlatform,
    benchmark_version: str,
    sampling_date: date,
) -> set[str]:
    completed: set[str] = set()

    for record in records:
        if record.observer_id != observer_id:
            continue

        if record.platform != platform:
            continue

        if record.benchmark_version != benchmark_version:
            continue

        record_date = (
            record.started_at_utc
            .astimezone(timezone.utc)
            .date()
        )

        if record_date != sampling_date:
            continue

        if record.generation_failed:
            continue

        if record.interrupted:
            continue

        if record.completed_at_utc is None:
            continue

        completed.add(record.prompt_id)

    return completed


def consumer_next(
    args: argparse.Namespace,
) -> int:
    try:
        now = parse_now_utc(
            args.now_utc
        )

        if args.sampling_date is None:
            sampling_date = now.date()
        else:
            sampling_date = parse_sampling_date(
                args.sampling_date
            )

        observer_id = args.observer_id

        if not observer_id:
            config = ObserverConfig.from_environment()
            observer_id = config.observer_id

        platform = ConsumerPlatform(
            args.platform
        )

        policy = SamplingPolicy(
            bucket_hours=args.bucket_hours,
            samples_per_bucket=args.samples_per_bucket,
            edge_guard_minutes=args.edge_guard_minutes,
        )

        schedule = build_prompt_bank_schedule(
            sampling_date,
            observer_id=observer_id,
            benchmark_version=args.benchmark_version,
            prompt_bank_path=args.prompt_bank,
            sampling_policy=policy,
        )

        store = ConsumerProbeSQLiteStore(
            args.storage
        )

        completed = completed_prompt_ids_for_day(
            store.load_all(),
            observer_id=observer_id,
            platform=platform,
            benchmark_version=args.benchmark_version,
            sampling_date=sampling_date,
        )

        due = find_due_probe(
            schedule,
            now_utc=now,
            completed_prompt_ids=completed,
            grace_minutes=args.grace_minutes,
        )

        upcoming = None

        if due is None:
            upcoming = find_next_probe(
                schedule,
                now_utc=now,
                completed_prompt_ids=completed,
            )

        if due is not None:
            status = "due"
            item = due.item

            item_payload = {
                "scheduled_at_utc": (
                    item.scheduled_at_utc.isoformat()
                ),
                "prompt_id": item.benchmark.prompt_id,
                "category": (
                    item.benchmark.category.value
                ),
                "prompt": item.benchmark.prompt,
                "overdue_by_ms": round(
                    due.overdue_by.total_seconds()
                    * 1000
                ),
            }

        elif upcoming is not None:
            status = "upcoming"
            item = upcoming

            starts_in = (
                item.scheduled_at_utc
                - now
            )

            item_payload = {
                "scheduled_at_utc": (
                    item.scheduled_at_utc.isoformat()
                ),
                "prompt_id": item.benchmark.prompt_id,
                "category": (
                    item.benchmark.category.value
                ),
                "prompt": item.benchmark.prompt,
                "starts_in_ms": round(
                    starts_in.total_seconds()
                    * 1000
                ),
            }

        else:
            status = "none"
            item_payload = None

        if args.json:
            payload = {
                "schema_version": "0.1",
                "status": status,
                "now_utc": now.isoformat(),
                "schedule_date": (
                    sampling_date.isoformat()
                ),
                "observer_id": observer_id,
                "platform": platform.value,
                "benchmark_version": (
                    args.benchmark_version
                ),
                "completed_today": len(completed),
                "item": item_payload,
            }

            print(
                json.dumps(
                    payload,
                    indent=2,
                    ensure_ascii=False,
                )
            )

            return 0

        print("=== DLLO CONSUMER NEXT ===")
        print(f"Now UTC:           {now.isoformat()}")
        print(f"Schedule date:     {sampling_date}")
        print(f"Observer:          {observer_id}")
        print(f"Platform:          {platform.value}")
        print(f"Completed today:   {len(completed)}")

        if due is not None:
            print("Status:            due")
            print(
                f"Scheduled:         "
                f"{due.item.scheduled_at_utc.isoformat()}"
            )
            print(
                f"Overdue by:        "
                f"{due.overdue_by.total_seconds() / 60:.1f} min"
            )
            print(
                f"Prompt ID:         "
                f"{due.item.benchmark.prompt_id}"
            )
            print(
                f"Category:          "
                f"{due.item.benchmark.category.value}"
            )
            print()
            print("Benchmark prompt:")
            print(due.item.benchmark.prompt)

            return 0

        if upcoming is not None:
            starts_in = (
                upcoming.scheduled_at_utc
                - now
            )

            print("Status:            upcoming")
            print(
                f"Scheduled:         "
                f"{upcoming.scheduled_at_utc.isoformat()}"
            )
            print(
                f"Starts in:         "
                f"{starts_in.total_seconds() / 60:.1f} min"
            )
            print(
                f"Prompt ID:         "
                f"{upcoming.benchmark.prompt_id}"
            )
            print(
                f"Category:          "
                f"{upcoming.benchmark.category.value}"
            )
            print()
            print("Benchmark prompt:")
            print(upcoming.benchmark.prompt)

            return 0

        print("Status:            none")
        print(
            "No actionable or upcoming probe "
            "remains in this schedule."
        )

        return 0

    except (
        ConsumerProbeStoreError,
        ConsumerScheduleError,
        ObserverConfigError,
        PromptBankError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def consumer_bridge(
    args: argparse.Namespace,
) -> int:
    try:
        observer_id = args.observer_id

        if not observer_id:
            config = ObserverConfig.from_environment()
            observer_id = config.observer_id

        bridge_config = BridgeConfig(
            observer_id=observer_id,
            platform=ConsumerPlatform(
                args.platform
            ),
            benchmark_version=args.benchmark_version,
            prompt_bank_path=args.prompt_bank,
            storage_path=args.storage,
            bucket_hours=args.bucket_hours,
            samples_per_bucket=args.samples_per_bucket,
            edge_guard_minutes=args.edge_guard_minutes,
            grace_minutes=args.grace_minutes,
        )

        serve(
            bridge_config,
            host=args.host,
            port=args.port,
            collector_static_root=(
                args.collector_static_root
            ),
        )

        return 0

    except (
        ObserverConfigError,
        ValueError,
        OSError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2



def agent_test(
    args: argparse.Namespace,
) -> int:
    try:
        observer_id, region_code = (
            resolve_observer_identity(args)
        )

        runner = AgentLabProtocolRunner(
            observer_id=observer_id,
            region_code=region_code,
            suite_root=args.suite_bank,
            task_root=args.task_bank,
        )

        result = runner.run(
            base_url=args.base_url,
            generated_at_utc=datetime.now(timezone.utc),
        )

        artifact = result.to_artifact()
        qualification = qualify_agent_observation(
            artifact
        )

        if args.output is not None:
            write_agent_lab_run_artifact(
                artifact,
                args.output,
            )

        report = result.report

        print("=== DLLO AGENT LAB ===")
        print(
            f"Target:            "
            f"{result.session.target.target_id}"
        )
        print(
            f"Suite:             "
            f"{report.suite_id} v{report.suite_version}"
        )
        print(
            f"Observer:          "
            f"{result.session.observer_id}"
        )
        print(
            f"Observed from:     "
            f"{result.session.region_code}"
        )
        print(
            f"Observatory:       "
            f"temporal="
            f"{'yes' if qualification.temporal_eligible else 'no'} "
            f"geographic="
            f"{'yes' if qualification.geographic_eligible else 'no'}"
        )
        print(f"Tasks:             {report.total_tasks}")
        print(f"Passed:            {report.passed_tasks}")
        print(
            f"Pass rate:         "
            f"{format_rate(report.pass_rate)}"
        )
        print(
            f"Median latency:    "
            f"{format_ms(report.median_latency_ms)}"
        )

        return 0

    except (
        AgentLabProtocolRunnerError,
        ObserverConfigError,
        OSError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2



def agent_compare(
    args: argparse.Namespace,
) -> int:
    try:
        baseline = load_agent_lab_run_artifact(
            args.baseline,
        )
        candidate = load_agent_lab_run_artifact(
            args.candidate,
        )

        comparison = compare_agent_lab_runs(
            candidate,
            baseline,
        )

        pass_rate_delta = (
            "n/a"
            if comparison.pass_rate_delta is None
            else f"{comparison.pass_rate_delta:+.1%}"
        )
        latency_delta = (
            "n/a"
            if comparison.median_latency_ms_delta
            is None
            else (
                f"{comparison.median_latency_ms_delta:+.1f} ms"
            )
        )

        print("=== DLLO AGENT COMPARISON ===")
        print(
            f"Target:             "
            f"{baseline.session.target.target_id}"
        )
        print(
            f"Suite:              "
            f"{baseline.session.suite_id} "
            f"v{baseline.session.suite_version}"
        )
        print(
            f"Baseline session:   "
            f"{comparison.baseline_session_id}"
        )
        print(
            f"Candidate session:  "
            f"{comparison.candidate_session_id}"
        )
        print()
        print(
            f"Tasks compared:     "
            f"{comparison.total_tasks}"
        )
        print(
            f"Improved:           "
            f"{comparison.improvements}"
        )
        print(
            f"Regressed:          "
            f"{comparison.regressions}"
        )
        print(
            f"Unchanged:          "
            f"{comparison.unchanged}"
        )
        print()
        print(
            f"Pass rate delta:    "
            f"{pass_rate_delta}"
        )
        print(
            f"Median latency:     "
            f"{latency_delta}"
        )
        print(
            f"Retries:            "
            f"{comparison.retry_delta:+d}"
        )
        print(
            f"Human interventions:"
            f"{comparison.human_intervention_delta:+d}"
        )
        print()
        print("Changed tasks:")

        changed = [
            change
            for change in comparison.task_changes
            if change.transition.value
            in {
                "pass-to-fail",
                "fail-to-pass",
            }
        ]

        if not changed:
            print("  None")

        for change in changed:
            transition = {
                "pass-to-fail": "PASS -> FAIL",
                "fail-to-pass": "FAIL -> PASS",
            }[change.transition.value]

            print(
                f"  {change.task_id}: "
                f"{transition}"
            )

        return 0

    except (
        AgentLabArtifactIOError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def agent_compare_temporal(
    args: argparse.Namespace,
) -> int:
    try:
        baseline = load_agent_lab_run_artifact(
            args.baseline,
        )
        candidate = load_agent_lab_run_artifact(
            args.candidate,
        )

        temporal_comparison = (
            compare_temporal_agent_observations(
                candidate,
                baseline,
            )
        )
        comparison = temporal_comparison.run_comparison

        pass_rate_delta = (
            "n/a"
            if comparison.pass_rate_delta is None
            else f"{comparison.pass_rate_delta:+.1%}"
        )
        latency_delta = (
            "n/a"
            if comparison.median_latency_ms_delta is None
            else (
                f"{comparison.median_latency_ms_delta:+.1f} ms"
            )
        )

        print("=== DLLO AGENT TEMPORAL COMPARISON ===")
        print(
            f"Target:             "
            f"{baseline.session.target.target_id}"
        )
        print(
            f"Suite:              "
            f"{baseline.session.suite_id} "
            f"v{baseline.session.suite_version}"
        )
        print(
            f"Observer:           "
            f"{temporal_comparison.observer_id}"
        )
        print(
            f"Observed from:      "
            f"{temporal_comparison.region_code}"
        )
        print(
            f"Baseline observed:  "
            f"{temporal_comparison.baseline_started_at_utc.isoformat()}"
        )
        print(
            f"Candidate observed: "
            f"{temporal_comparison.candidate_started_at_utc.isoformat()}"
        )
        print()
        print(
            f"Tasks compared:     "
            f"{comparison.total_tasks}"
        )
        print(
            f"Improved:           "
            f"{comparison.improvements}"
        )
        print(
            f"Regressed:          "
            f"{comparison.regressions}"
        )
        print(
            f"Unchanged:          "
            f"{comparison.unchanged}"
        )
        print()
        print(
            f"Pass rate delta:    "
            f"{pass_rate_delta}"
        )
        print(
            f"Median latency:     "
            f"{latency_delta}"
        )
        print(
            f"Retries:            "
            f"{comparison.retry_delta:+d}"
        )
        print(
            f"Human interventions:"
            f"{comparison.human_intervention_delta:+d}"
        )

        return 0

    except (
        AgentLabArtifactIOError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2

def agent_compare_geographic(
    args: argparse.Namespace,
) -> int:
    try:
        baseline = load_agent_lab_run_artifact(
            args.baseline,
        )
        candidate = load_agent_lab_run_artifact(
            args.candidate,
        )

        geographic_comparison = (
            compare_geographic_agent_observations(
                candidate,
                baseline,
                max_observation_skew=timedelta(
                    seconds=args.max_observation_skew_seconds,
                ),
            )
        )
        comparison = geographic_comparison.run_comparison

        pass_rate_delta = (
            "n/a"
            if comparison.pass_rate_delta is None
            else f"{comparison.pass_rate_delta:+.1%}"
        )
        latency_delta = (
            "n/a"
            if comparison.median_latency_ms_delta is None
            else (
                f"{comparison.median_latency_ms_delta:+.1f} ms"
            )
        )

        print("=== DLLO AGENT GEOGRAPHIC COMPARISON ===")
        print(
            f"Target:                "
            f"{baseline.session.target.target_id}"
        )
        print(
            f"Suite:                 "
            f"{baseline.session.suite_id} "
            f"v{baseline.session.suite_version}"
        )
        print(
            f"Baseline observer:     "
            f"{geographic_comparison.baseline_observer_id}"
        )
        print(
            f"Candidate observer:    "
            f"{geographic_comparison.candidate_observer_id}"
        )
        print(
            f"Observed from baseline:  "
            f"{geographic_comparison.baseline_region_code}"
        )
        print(
            f"Observed from candidate: "
            f"{geographic_comparison.candidate_region_code}"
        )
        print(
            f"Baseline observed:     "
            f"{geographic_comparison.baseline_started_at_utc.isoformat()}"
        )
        print(
            f"Candidate observed:    "
            f"{geographic_comparison.candidate_started_at_utc.isoformat()}"
        )
        print(
            f"Observation skew:      "
            f"{geographic_comparison.observation_skew.total_seconds():.2f} s"
        )
        print(
            f"Maximum allowed skew: "
            f"{geographic_comparison.max_observation_skew.total_seconds():.2f} s"
        )
        print()
        print(
            f"Tasks compared:        "
            f"{comparison.total_tasks}"
        )
        print(
            f"Improved:              "
            f"{comparison.improvements}"
        )
        print(
            f"Regressed:             "
            f"{comparison.regressions}"
        )
        print(
            f"Unchanged:             "
            f"{comparison.unchanged}"
        )
        print()
        print(
            f"Pass rate delta:       "
            f"{pass_rate_delta}"
        )
        print(
            f"Median latency:        "
            f"{latency_delta}"
        )
        print(
            f"Retries:               "
            f"{comparison.retry_delta:+d}"
        )
        print(
            f"Human interventions:   "
            f"{comparison.human_intervention_delta:+d}"
        )

        return 0

    except (
        AgentLabArtifactIOError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2

def agent_pairs_geographic(
    args: argparse.Namespace,
) -> int:
    try:
        history = AgentLabRunHistory(
            args.history_root
        )

        if args.target is None:
            artifacts = history.load_all()
        else:
            artifacts = history.for_target(
                args.target
            )

        max_observation_skew = timedelta(
            seconds=args.max_observation_skew_seconds,
        )

        pairs = (
            discover_geographic_agent_observation_pairs(
                artifacts,
                max_observation_skew=max_observation_skew,
            )
        )

        print("=== DLLO AGENT GEOGRAPHIC PAIRS ===")
        print(
            f"Runs:               "
            f"{len(artifacts)}"
        )
        print(
            f"Pairs:              "
            f"{len(pairs)}"
        )

        if args.target is not None:
            print(
                f"Target filter:      "
                f"{args.target}"
            )

        print(
            f"Maximum skew:       "
            f"{max_observation_skew.total_seconds():.2f} s"
        )

        for pair in pairs:
            print()
            print(
                f"Baseline session:   "
                f"{pair.baseline_session_id}"
            )
            print(
                f"Candidate session:  "
                f"{pair.candidate_session_id}"
            )
            print(
                f"Comparable:         "
                f"{'yes' if pair.comparable else 'no'}"
            )

            for reason in pair.reasons:
                print(
                    f"Reason:             "
                    f"{reason}"
                )

        return 0

    except (
        AgentLabArtifactIOError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def agent_pairs_temporal(
    args: argparse.Namespace,
) -> int:
    try:
        history = AgentLabRunHistory(
            args.history_root
        )

        if args.target is None:
            artifacts = history.load_all()
        else:
            artifacts = history.for_target(
                args.target
            )

        pairs = (
            discover_temporal_agent_observation_pairs(
                artifacts
            )
        )

        print("=== DLLO AGENT TEMPORAL PAIRS ===")
        print(
            f"Runs:               "
            f"{len(artifacts)}"
        )
        print(
            f"Pairs:              "
            f"{len(pairs)}"
        )

        if args.target is not None:
            print(
                f"Target filter:      "
                f"{args.target}"
            )

        for pair in pairs:
            print()
            print(
                f"Baseline session:   "
                f"{pair.baseline_session_id}"
            )
            print(
                f"Candidate session:  "
                f"{pair.candidate_session_id}"
            )
            print(
                f"Comparable:         "
                f"{'yes' if pair.comparable else 'no'}"
            )

            for reason in pair.reasons:
                print(
                    f"Reason:             "
                    f"{reason}"
                )

        return 0

    except (
        AgentLabArtifactIOError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def agent_history(
    args: argparse.Namespace,
) -> int:
    try:
        history = AgentLabRunHistory(
            args.history_root
        )

        if args.target is None:
            artifacts = history.load_all()
        else:
            artifacts = history.for_target(
                args.target
            )

        print("=== DLLO AGENT RUN HISTORY ===")
        print(
            f"Runs:               "
            f"{len(artifacts)}"
        )

        if args.target is not None:
            print(
                f"Target filter:      "
                f"{args.target}"
            )

        if not artifacts:
            print()
            print("No Agent Lab runs found.")
            return 0

        for artifact in artifacts:
            session = artifact.session
            report = artifact.technical_report

            print()
            print(
                f"Started:            "
                f"{session.started_at_utc.isoformat()}"
            )
            print(
                f"Session:            "
                f"{session.session_id}"
            )
            print(
                f"Target:             "
                f"{session.target.target_id}"
            )
            print(
                f"Suite:              "
                f"{session.suite_id} "
                f"v{session.suite_version}"
            )

            qualification = qualify_agent_observation(
                artifact
            )

            print(
                f"Observer:            "
                f"{session.observer_id or 'n/a'}"
            )
            print(
                f"Observed from:       "
                f"{session.region_code or 'n/a'}"
            )
            print(
                f"Observatory:         "
                f"temporal="
                f"{'yes' if qualification.temporal_eligible else 'no'} "
                f"geographic="
                f"{'yes' if qualification.geographic_eligible else 'no'}"
            )

            if qualification.reasons:
                print(
                    "Observatory reasons: "
                    + ", ".join(
                        qualification.reasons
                    )
                )

            print(
                f"Tasks:              "
                f"{report.total_tasks}"
            )
            print(
                f"Pass rate:          "
                f"{format_rate(report.pass_rate)}"
            )

        return 0

    except AgentLabArtifactIOError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2

def task_list(
    args: argparse.Namespace,
) -> int:
    try:
        tasks = TaskBank(
            args.task_bank
        ).load_enabled()

        print("=== DLLO BENCHMARK TASKS ===")
        print(f"Tasks:             {len(tasks)}")

        for task in tasks:
            capabilities = ", ".join(
                sorted(
                    capability.value
                    for capability
                    in task.required_capabilities
                )
            )

            print(
                f"{task.task_id} "
                f"[{task.family.value}/"
                f"{task.category.value}/"
                f"{task.difficulty.value}] "
                f"capabilities={capabilities}"
            )

        return 0

    except TaskBankError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def task_show(
    args: argparse.Namespace,
) -> int:
    try:
        tasks = TaskBank(
            args.task_bank
        ).load_all()

        task = next(
            (
                candidate
                for candidate in tasks
                if candidate.task_id == args.task_id
            ),
            None,
        )

        if task is None:
            print(
                f"Task not found: {args.task_id}",
                file=sys.stderr,
            )
            return 2

        capabilities = ", ".join(
            sorted(
                capability.value
                for capability
                in task.required_capabilities
            )
        )

        print("=== DLLO BENCHMARK TASK ===")
        print(f"Task ID:           {task.task_id}")
        print(
            f"Benchmark version: {task.benchmark_version}"
        )
        print(f"Family:            {task.family.value}")
        print(f"Category:          {task.category.value}")
        print(
            f"Difficulty:        {task.difficulty.value}"
        )
        print(f"Evaluator:         {task.evaluator_id}")
        print(f"Capabilities:      {capabilities}")
        print(
            f"Fixture:           "
            f"{task.fixture_id or 'none'}"
        )
        print(
            f"Enabled:           "
            f"{str(task.enabled).lower()}"
        )
        print()
        print("Task:")
        print(task.task)
        print()
        print("Success criteria:")

        for criterion in task.success_criteria:
            print(
                f"- {criterion.criterion_id}: "
                f"{criterion.description}"
            )

        return 0

    except TaskBankError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        return run_benchmark(args)

    if args.command == "consumer-import":
        return consumer_import(args)

    if args.command == "consumer-summary":
        return consumer_summary(args)

    if args.command == "consumer-detect":
        return consumer_detect(args)

    if args.command == "consumer-schedule":
        return consumer_schedule(args)

    if args.command == "consumer-next":
        return consumer_next(args)

    if args.command == "consumer-bridge":
        return consumer_bridge(args)

    if args.command == "agent-test":
        return agent_test(args)

    if args.command == "agent-compare":
        return agent_compare(args)

    if args.command == "agent-compare-temporal":
        return agent_compare_temporal(args)

    if args.command == "agent-compare-geographic":
        return agent_compare_geographic(args)

    if args.command == "agent-history":
        return agent_history(args)

    if args.command == "agent-pairs-temporal":
        return agent_pairs_temporal(args)

    if args.command == "agent-pairs-geographic":
        return agent_pairs_geographic(args)

    if args.command == "task-list":
        return task_list(args)

    if args.command == "task-show":
        return task_show(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
