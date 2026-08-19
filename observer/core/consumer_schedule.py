from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from consumer_probe.queue import build_daily_queue
from consumer_probe.sampling import SamplingPolicy
from observer.core.prompt_bank import PromptBank
from schemas.benchmark import BenchmarkPrompt


class ConsumerScheduleError(Exception):
    """Raised when a Consumer Probe schedule cannot be built."""


@dataclass(frozen=True)
class ScheduledBenchmark:
    scheduled_at_utc: datetime
    benchmark: BenchmarkPrompt


@dataclass(frozen=True)
class ConsumerDailySchedule:
    sampling_date: date
    observer_id: str
    benchmark_version: str
    items: list[ScheduledBenchmark]


def build_prompt_bank_schedule(
    sampling_date: date,
    *,
    observer_id: str,
    benchmark_version: str,
    prompt_bank_path: Path = Path("benchmark/prompts"),
    sampling_policy: SamplingPolicy | None = None,
) -> ConsumerDailySchedule:
    """
    Build a deterministic daily Consumer Probe schedule from the
    enabled prompts in the real benchmark bank.

    Only prompts matching benchmark_version are eligible.
    """
    prompt_bank = PromptBank(prompt_bank_path)
    prompts = prompt_bank.load_enabled()

    eligible = [
        prompt
        for prompt in prompts
        if prompt.benchmark_version == benchmark_version
    ]

    if not eligible:
        raise ConsumerScheduleError(
            "No enabled benchmark prompts found for "
            f"version {benchmark_version}."
        )

    prompts_by_id = {
        prompt.prompt_id: prompt
        for prompt in eligible
    }

    queue = build_daily_queue(
        sampling_date,
        observer_id=observer_id,
        prompt_ids=list(prompts_by_id),
        sampling_policy=sampling_policy,
    )

    items = [
        ScheduledBenchmark(
            scheduled_at_utc=item.scheduled_at_utc,
            benchmark=prompts_by_id[item.prompt_id],
        )
        for item in queue
    ]

    return ConsumerDailySchedule(
        sampling_date=sampling_date,
        observer_id=observer_id,
        benchmark_version=benchmark_version,
        items=items,
    )
