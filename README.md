# Distributed LLM Observatory

**Distributed LLM Observatory (DLLO)** is an open-source framework for producing reproducible observations of LLMs, AI agents, and AI systems across time, regions, benchmark versions, and operating conditions.

DLLO is designed around a simple rule:

> **Measure what can be observed. Do not infer causes that the evidence cannot establish.**

The project combines deterministic benchmark execution, observer-owned evidence, Agent Lab testing, local consumer telemetry, persistent run artifacts, and temporal/geographic comparison tools.

---

## Why DLLO exists

AI systems can change behavior over time.

Latency may vary. Tool use may change. Failure rates may move. A model observed from one region may behave differently from the same model observed elsewhere.

Those differences are interesting, but observation and explanation are not the same thing.

DLLO therefore records:

- what was tested;
- when it was tested;
- where the observation originated;
- which benchmark and protocol version were used;
- what the system under test actually did;
- what evidence the observer collected;
- what changed between comparable observations.

DLLO deliberately avoids unsupported claims about datacenter location, provider routing, saturation, throttling, infrastructure causes, or other mechanisms that cannot be directly observed.

For example:

> **Observed from CL-Los-Lagos**

does not mean:

> **Served from a datacenter in Chile.**

---

## Project status

DLLO is under active development, but several core layers are now operational.

### Stable

- benchmark and task schemas;
- deterministic evaluation infrastructure;
- observer-owned evidence collection;
- local SUT execution protocol;
- **Agent Protocol Core 1.0**;
- Agent Lab test sessions;
- technical reports;
- persistent Agent Lab run artifacts;
- run history;
- artifact integrity validation;
- Observatory qualification;
- temporal observation comparison;
- geographic observation comparison;
- observation pair discovery;
- exact history/session resolution;
- human-readable comparison output;
- machine-readable JSON output.

### In active development

- broader Agent Lab user experience;
- Agent Starter hardware/capability guidance;
- additional benchmark families;
- larger distributed observation datasets;
- Observatory visualization and analysis;
- distributed observer coordination;
- richer consumer-facing measurement workflows.

A centralized global Observatory service and public dashboard are not yet the core production target of the current repository.

---

# Agent Lab

Agent Lab is the part of DLLO focused on testing AI agents.

It is being developed around two complementary workflows.

## Test Your Agent

The currently implemented workflow allows an agent to be connected to DLLO and evaluated through a stable protocol.

Conceptually:

```text
Agent
  |
  v
Compatibility
  |
  v
Agent Test Session
  |
  v
Agent Protocol Core
  |
  v
Observer-owned evidence
  |
  v
Evaluation
  |
  v
Technical Report
  |
  v
AgentLabRunArtifact
  |
  v
History
  |
  v
Observatory qualification
  |
  v
Temporal / Geographic comparison
```

The system under test performs the task.

The observer collects evidence.

The evaluator evaluates that evidence.

The Observatory compares compatible observations.

These responsibilities are intentionally separate.

## Agent Starter

Agent Starter is the complementary Agent Lab direction for helping users determine what kind of agent stack can reasonably run on their hardware.

The foundations include hardware and capability profiling, while the complete user-facing workflow remains under development.

The design also considers mobile devices, where browser/app access to hardware and operating-system information may be more restricted than on desktop systems.

---

# Agent Protocol Core 1.0

**Agent Protocol Core 1.0 is stable.**

It is the behavioral freeze of the qualified `agent-protocol-core` benchmark sequence developed through versions 0.1-0.10.

The protocol currently covers:

- exact output evaluation;
- instruction following;
- structured output;
- observed tool actions;
- semantic tool selection;
- ordered action sequences;
- runtime data propagation between tools;
- failure handling and recovery;
- conditional runtime branching;
- multi-branch runtime decisions.

Version 1.0 introduces no new benchmark capability over 0.10. It freezes the qualified behavior into a stable protocol contract.

See:

[`docs/observer-protocol.md`](docs/observer-protocol.md)

---

## Observer / SUT boundary

DLLO does not allow the system under test to certify itself.

The SUT receives only information required to execute the task.

Observer-owned information is kept separate, including:

- expected actions;
- expected tool selection;
- expected runtime propagation;
- recovery expectations;
- branch expectations;
- criterion evidence;
- verifier logic;
- PASS/FAIL verdicts.

Runtime information becomes visible to the SUT only through the execution mechanisms defined by the task.

The intended chain is:

```text
Task
  ->
SUT execution
  ->
Observer evidence collection
  ->
Evaluation
```

not:

```text
SUT
  ->
self-declared success
```

---

# Local SUT Protocol

Agents can be tested through a local HTTP protocol.

The current protocol uses loopback-local communication and exposes a small public contract to the system under test.

The observer remains responsible for benchmark fixtures, evidence, expectations, and evaluation.

This allows DLLO to test real agent behavior without exposing verifier-only information to the agent.

---

# Observatory layer

An Agent Lab run can become an Observatory observation when it carries sufficient provenance.

Typical provenance includes:

```text
observer_id
region_code
started_at_utc
target
suite_id
suite_version
task coverage
```

DLLO distinguishes two concepts:

```text
valid run artifact
!=
Observatory-eligible observation
```

A historical or legacy artifact can remain valid and useful even when it lacks sufficient provenance for Observatory-qualified comparisons.

Qualification is derived from the artifact rather than stored as an independent claim.

---

## Temporal comparisons

A temporal Observatory comparison asks:

> What changed when a compatible target was observed again later from the same observation context?

Temporal comparison requires compatible observations, including:

- same target;
- same benchmark suite;
- same suite version;
- compatible task coverage;
- complete required provenance;
- same observer identity;
- same observation region;
- candidate observation strictly after the baseline.

The result describes observed change.

It does not assign a cause.

---

## Geographic comparisons

A geographic Observatory comparison asks:

> What differences were observed from different regions under compatible benchmark conditions?

Geographic comparison requires:

- same target;
- same benchmark suite;
- same suite version;
- compatible task coverage;
- complete required provenance;
- different observation regions;
- observations sufficiently close in time.

The maximum accepted observation-time skew is always supplied explicitly by the caller.

DLLO intentionally has no hidden geographic comparison threshold.

---

# Observation pair discovery

As an observation history grows, manually finding comparable runs becomes difficult.

DLLO can discover candidate temporal and geographic pairs.

Pair discovery:

- uses deterministic ordering;
- delegates comparability to the canonical comparison rules;
- keeps rejected pairs visible;
- records reasons when a pair is not comparable;
- does not automatically select a baseline;
- does not automatically select a candidate;
- does not use a magic `latest` observation.

The user remains responsible for choosing which comparable pair to inspect.

---

# Agent Lab history

Agent Lab run artifacts can be persisted and loaded as history.

History supports exact session resolution using UUIDs.

The design intentionally avoids:

- fuzzy session matching;
- UUID prefixes;
- implicit latest-run selection;
- silent baseline selection.

This makes a discovered pair reproducible later using the exact observation identifiers.

---

# Machine-readable Observatory

DLLO supports JSON output for the principal history and comparison workflows.

Current machine-readable commands include:

```text
agent-history --json

agent-pairs-temporal --json

agent-pairs-geographic --json

agent-compare-temporal --json

agent-compare-temporal-history --json

agent-compare-geographic --json

agent-compare-geographic-history --json
```

This creates a machine-readable flow such as:

```text
history
  |
  v
pair discovery
  |
  v
explicit pair selection
  |
  v
canonical comparison
  |
  v
JSON
```

Rejected pairs remain present in pair-discovery JSON.

Missing provenance is represented as JSON `null`, rather than a human-display placeholder such as `"n/a"`.

Geographic comparison output also preserves the explicit maximum observation skew used for the comparison.

---

# Consumer Probe

DLLO also contains a Consumer Probe subsystem for observations made through consumer-facing AI interfaces.

Its design principles include:

- human-in-the-loop interaction;
- no automatic prompt submission;
- no scraping of private interfaces;
- no collection of browser session tokens or cookies;
- no use of private provider endpoints;
- no rate-limit bypass;
- local-first telemetry and history.

Consumer Probe can record local timing, outcome, schedule, and supported browser/OS telemetry while keeping the distinction between what the observer can measure and what the provider infrastructure actually does.

---

# Measurement principles

## Neutral observation

A measurement describes what was observed.

For example, increased latency is evidence of increased latency.

It is not by itself evidence of:

- server saturation;
- routing changes;
- throttling;
- capacity management;
- model replacement;
- infrastructure failure.

Those may become hypotheses, but they require additional evidence.

## Reproducibility

An observation should contain enough provenance to reconstruct the conditions under which it was produced.

## Comparable measurements

Measurements should only be compared when their semantics are compatible.

Benchmark versions, task coverage, observation provenance, and measurement methods must not be silently mixed.

## No hidden selection

The Observatory should not silently choose:

- the best run;
- the newest run;
- a baseline;
- a comparison pair;
- a geographic time threshold.

Selection remains explicit.

## Privacy by design

DLLO aims to collect only information required for measurement and reproducibility.

See:

[`docs/privacy.md`](docs/privacy.md)

---

# Target taxonomy

DLLO distinguishes between several kinds of systems under test:

```text
FOUNDATION_MODEL
AGENT
AI_SYSTEM
```

Targets can declare capabilities such as:

```text
text
vision
audio_input
speech_output
memory
tools
browser
filesystem
code_execution
```

Compatibility is evaluated before executing workloads that require unavailable capabilities.

---

# Repository structure

```text
distributed-llm-observatory/
|
|-- analysis/          Analysis and statistical tooling
|-- benchmark/         Prompts, tasks, suites, and benchmark assets
|-- consumer_probe/    Consumer-interface observation subsystem
|-- docs/              Architecture, methodology, privacy, protocols
|-- judges/            Evaluation rubrics and validators
|-- observer/          Core observer and Agent Lab implementation
|-- pricing/           Pricing and economic measurement models
|-- schemas/           Shared structured data models
|-- server/            Service-side foundations
|-- tests/             Unit and integration tests
|-- web/collector/     Browser-side collection components
|
|-- README.md
|-- CONTRIBUTING.md
|-- LICENSE
`-- pyproject.toml
```

The architecture intentionally keeps execution, evidence, evaluation, storage, and interpretation as separate concerns.

See:

[`docs/architecture.md`](docs/architecture.md)

---

# Development

DLLO requires **Python 3.10 or newer**.

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project and development dependencies:

```bash
pip install -e ".[dev]"
```

Run the complete test suite:

```bash
pytest -q
```

Run Ruff:

```bash
ruff check .
```

The project uses automated tests extensively to protect benchmark compatibility, historical suite resolution, observer/SUT boundaries, evidence semantics, artifact integrity, and comparison behavior.

---

# Documentation

Key documentation currently includes:

- [`docs/architecture.md`](docs/architecture.md) - system architecture
- [`docs/methodology.md`](docs/methodology.md) - measurement methodology
- [`docs/observer-protocol.md`](docs/observer-protocol.md) - Observer and Agent Protocol
- [`docs/privacy.md`](docs/privacy.md) - privacy principles
- [`docs/quality-rubric.md`](docs/quality-rubric.md) - response-quality evaluation
- [`docs/roadmap.md`](docs/roadmap.md) - project roadmap
- [`benchmark/README.md`](benchmark/README.md) - benchmark organization

---

# Scientific scope

DLLO is intended to support investigation of patterns such as:

- temporal behavioral variation;
- regional differences in observed behavior;
- changes in task success;
- changes in latency;
- changes in retry behavior;
- changes in human-intervention requirements;
- elevated failure rates;
- instability across repeated observations;
- economic changes across comparable workloads.

These observations can support hypotheses about underlying mechanisms.

The Observatory should not claim those mechanisms as facts unless independent evidence supports them.

---

# Current direction

The current development direction is centered on completing the loop:

```text
connect agent
  ->
check compatibility
  ->
run stable protocol
  ->
collect observer-owned evidence
  ->
generate technical report
  ->
persist observation
  ->
discover comparable history
  ->
compare selected runs
  ->
analyze changes over time and geography
```

The next stages focus increasingly on turning this infrastructure into a coherent Observatory experience and on collecting meaningful distributed observations.

---

# What DLLO is not

DLLO is not intended to be:

- a provider leaderboard based on a single global score;
- a system that automatically declares one model or agent "best";
- a causal inference engine for undocumented provider infrastructure;
- an agent self-certification framework;
- a scraping system for private consumer interfaces;
- a mechanism for bypassing provider restrictions.

The project is an observation and measurement framework.

---

# Contributing

Contributions are welcome.

Please read:

[`CONTRIBUTING.md`](CONTRIBUTING.md)

before submitting changes.

---

# License

Distributed LLM Observatory is released under the **MIT License**.

See:

[`LICENSE`](LICENSE)

---

## Core principle

> **Observe first. Compare carefully. Explain only when the evidence allows it.**
