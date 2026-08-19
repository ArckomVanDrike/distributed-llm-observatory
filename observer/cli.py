from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from consumer_probe.analytics import summarize
from consumer_probe.comparison import ComparisonPolicy
from consumer_probe.detection import detect_utc_bucket
from consumer_probe.importer import (
    ConsumerProbeImportError,
    import_export,
)
from consumer_probe.schemas import ConsumerPlatform
from consumer_probe.storage.sqlite import (
    ConsumerProbeSQLiteStore,
    ConsumerProbeStoreError,
)
from observer.core.benchmark_runner import BenchmarkRunner
from observer.core.config import ObserverConfig, ObserverConfigError
from observer.core.prompt_bank import PromptBank, PromptBankError
from observer.core.recording import build_observation_record
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


def consumer_summary(
    args: argparse.Namespace,
) -> int:
    try:
        store = ConsumerProbeSQLiteStore(
            args.storage
        )

        records = store.load_all()
        stats = summarize(records)

        print("=== DLLO CONSUMER SUMMARY ===")
        print(
            f"Samples:          "
            f"{stats.sample_count}"
        )
        print(
            f"Successful:       "
            f"{stats.successful_samples}"
        )
        print(
            f"Median TTFO:      "
            f"{format_ms(stats.median_ttfo_ms)}"
        )
        print(
            f"P95 TTFO:         "
            f"{format_ms(stats.p95_ttfo_ms)}"
        )
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
                f"TTFO ratio:        "
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

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
