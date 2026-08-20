# Distributed LLM Observatory

**Distributed LLM Observatory (DLLO)** is an open-source project for measuring how large language model behavior varies across time, geography, providers, prompts, and operating conditions.

The project is designed as a neutral measurement system. It does not assume why a model behaves differently; it records observations so that hypotheses can be tested against data.

## Goals

DLLO aims to provide reproducible measurements of:

- response quality
- latency and responsiveness
- failures and interruptions
- behavioral stability
- geographic and temporal variation
- economic efficiency
- provider and model differences

The Observatory separates **observation** from **interpretation**. For example, a measurement made from a particular region describes where the observation originated, not which datacenter or infrastructure served the request.

## Project Status

DLLO is currently under active development.

The `main` branch contains the foundational project structure, schemas, documentation, benchmark definitions, and subsystem scaffolding.

More advanced observer and Consumer Probe functionality is being developed and validated separately before being integrated into the main branch.

## Architecture

The repository is organized into several major areas:

    analysis/        Analysis and statistical tooling
    benchmark/       Benchmark definitions and prompt methodology
    consumer_probe/  Consumer-interface observation subsystem
    dashboard/       Future visualization layer
    docs/            Architecture, methodology, privacy, and protocol docs
    judges/          Evaluation rubrics and validators
    observer/        Core observation framework
    pricing/         Cost and pricing models
    schemas/         Shared structured data models
    server/          Future service-side components
    tests/           Unit and integration tests

The design intentionally keeps measurement, storage, evaluation, and interpretation as separate concerns.

See [`docs/architecture.md`](docs/architecture.md) for the architectural overview.

## Measurement Principles

DLLO follows several core principles.

### Neutral observation

Measurements should describe what was observed without assigning an unsupported cause.

A latency increase, for example, is evidence of a latency increase. It is not by itself evidence of server saturation, infrastructure routing, throttling, or any other specific mechanism.

### Reproducibility

Observations should carry enough provenance to determine:

- what was measured
- when it was measured
- where the observer was located
- which benchmark and prompt were used
- which measurement method produced the value

### Comparable measurements

Metrics should only be compared when their measurement semantics are compatible.

Different collection methods, benchmark versions, or measurement modes must not be silently mixed.

### Privacy by design

The project aims to collect the minimum information necessary for scientific analysis.

See [`docs/privacy.md`](docs/privacy.md).

## Benchmarking

Benchmark material lives under [`benchmark/`](benchmark/).

The benchmark design covers multiple task families so that observations are not dominated by a single workload type.

Evaluation methodology and quality criteria are documented separately from the measurement pipeline.

See:

- [`benchmark/README.md`](benchmark/README.md)
- [`docs/methodology.md`](docs/methodology.md)
- [`docs/quality-rubric.md`](docs/quality-rubric.md)

## Observer Protocol

Distributed observations require consistent rules for timestamps, regions, prompts, execution conditions, and metadata.

See [`docs/observer-protocol.md`](docs/observer-protocol.md).

## Development

DLLO requires Python 3.10 or newer.

Create a virtual environment:

    python -m venv .venv
    source .venv/bin/activate

Install the project with development dependencies:

    pip install -e ".[dev]"

Run the test suite:

    pytest

Run Ruff:

    ruff check .

## Documentation

Additional project documentation:

- [`docs/architecture.md`](docs/architecture.md) — system architecture
- [`docs/methodology.md`](docs/methodology.md) — measurement methodology
- [`docs/observer-protocol.md`](docs/observer-protocol.md) — distributed observation protocol
- [`docs/privacy.md`](docs/privacy.md) — privacy principles
- [`docs/quality-rubric.md`](docs/quality-rubric.md) — response-quality evaluation
- [`docs/roadmap.md`](docs/roadmap.md) — planned development

## Scientific Scope

DLLO can identify patterns such as:

- temporal performance variation
- regional differences in observed behavior
- changes in quality or latency distributions
- elevated error or interruption rates
- instability across repeated observations

These measurements can support hypotheses about underlying causes, but the Observatory should not claim infrastructure-level explanations that the available evidence cannot establish.

## Contributing

Contributions are welcome.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting changes.

## License

Distributed LLM Observatory is released under the MIT License.

See [`LICENSE`](LICENSE).
