from __future__ import annotations

import argparse
import sys
from pathlib import Path

from observer.core.benchmark_runner import BenchmarkRunner
from observer.core.config import ObserverConfig, ObserverConfigError
from observer.core.prompt_bank import PromptBank, PromptBankError
from observer.core.recording import build_observation_record
from observer.providers.mock import MockProvider
from observer.storage.sqlite import SQLiteObservationStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dllo",
        description="Distributed LLM Observatory observer node",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

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

        store = SQLiteObservationStore(config.storage_path)
        store.append(record)

        print(f"Observation ID: {record.observation_id}")
        print(f"Prompt:         {benchmark.prompt_id}")
        print(f"Provider:       {record.execution.provider}")
        print(f"Model:          {record.execution.model}")
        print(f"Region:         {record.observer.region_code}")
        print(f"Latency:        {record.execution.latency_ms:.2f} ms")
        print(f"Tokens/s:       {record.execution.tokens_per_second:.2f}")
        print(f"Storage:        {config.storage_path}")

        return 0

    except (ObserverConfigError, PromptBankError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        return run_benchmark(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
