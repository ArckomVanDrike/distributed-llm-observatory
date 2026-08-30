# Distributed LLM Observatory

**Build agents. Test agents. Observe how AI systems change.**

Distributed LLM Observatory (**DLLO**) is an open-source framework for building evidence-based agent configurations, testing real AI agents, and producing reproducible observations of LLMs and AI systems across time, regions, benchmark versions, and operating conditions.

> **Observe first. Compare carefully. Explain only when the evidence allows it.**

DLLO is built around three complementary workflows:

| Workflow | Question |
| --- | --- |
| **Agent Starter** | What kind of agent architecture and stack should I build? |
| **Test Your Agent** | Does my agent actually behave correctly? |
| **Observatory** | What changed between compatible observations? |

---

## What you can do with DLLO

### Build your agent — Agent Starter

**Agent Starter v1** helps turn user goals, constraints, observed capabilities, and explicit preferences into an evidence-backed agent architecture and concrete stack recommendation.

Supported goals:

- **Coding**
- **Knowledge / RAG**
- **Automation**
- **Voice**
- **Personal assistant**

The decision flow is intentionally explicit:

```text
USER GOAL
    ↓
REQUIRED CAPABILITIES
    ↓
HARD CONSTRAINTS
    ↓
OBSERVED ENVIRONMENT
    ↓
TECHNICAL FEASIBILITY
    ↓
SOFT PREFERENCES
    ↓
OPERATIONAL FIT
    ↓
CATALOG MATCHING
    ↓
RECOMMENDATION
```

Agent Starter includes:

- adaptive goal-specific questions;
- evidence provenance;
- hardware and compatibility input;
- candidate architecture generation;
- technical feasibility assessment;
- hard-constraint enforcement;
- decision-active soft preferences;
- explicit catalog snapshots;
- concrete stack resolution;
- recommendation alternatives;
- Why / Why Not explanations;
- final structured technical report.

Agent Starter does **not** silently choose a global winner.

Multiple architectures may remain valid when the evidence does not justify a unique recommendation.

#### Privacy and offline are different

Agent Starter models privacy, locality, and connectivity separately.

```text
private != offline
local execution != offline capability
```

For example, an architecture may keep source code local while still requiring network access for some runtime dependency.

When offline operation is required, candidate offline support must be explicitly established.

---

### Test your agent — Agent Lab

**Test Your Agent v1** connects an agent to DLLO and evaluates its behavior through a stable observer-controlled protocol.

```text
Agent
  ↓
Compatibility
  ↓
Agent Test Session
  ↓
Agent Protocol Core
  ↓
Observer-owned evidence
  ↓
Evaluation
  ↓
Technical Report
  ↓
Persistent Run Artifact
  ↓
History
  ↓
Observatory
```

The system under test performs the task.

The observer collects the evidence.

The evaluator evaluates that evidence.

The system under test does **not** certify itself.

Current protocol coverage includes:

- exact output;
- instruction following;
- structured output;
- tool selection;
- ordered action sequences;
- runtime data propagation;
- failure handling and recovery;
- conditional branching;
- multi-branch decisions.

**Agent Protocol Core 1.0 is stable.**

---

### Observe what changed — Observatory

DLLO turns sufficiently qualified run artifacts into reproducible observations.

The Observatory supports:

- persistent history;
- exact session resolution;
- observation qualification;
- temporal pair discovery;
- geographic pair discovery;
- temporal comparison;
- geographic comparison;
- human-readable output;
- machine-readable JSON output.

A comparison answers:

> **What changed?**

It does not automatically answer:

> **Why did it change?**

---

## Why DLLO exists

AI systems can change behavior across time and operating conditions.

Latency may vary. Tool use may change. Failure rates may move. The same target observed at different times or from different regions may produce different results.

Those differences are worth measuring.

But:

```text
observation != explanation
```

DLLO therefore records:

- what was tested;
- when it was tested;
- where the observation originated;
- which benchmark and protocol version were used;
- what the system under test actually did;
- what evidence the observer collected;
- what changed between comparable observations.

DLLO deliberately avoids unsupported claims about:

- provider routing;
- datacenter location;
- saturation;
- throttling;
- infrastructure causes;
- undocumented model changes.

For example:

> **Observed from CL-Los-Lagos**

does **not** mean:

> **Served from a datacenter in Chile.**

Region represents **observation provenance**, not inferred serving location.

---

## Project status

The principal DLLO v1 building blocks are operational.

| Component | Status |
| --- | --- |
| Agent Protocol Core 1.0 | **Stable** |
| Test Your Agent v1 | **Complete** |
| Agent Starter v1 | **Complete** |
| Observatory Dashboard v1 | **Complete** |
| Temporal comparison | **Operational** |
| Geographic comparison | **Operational** |
| Observation pair discovery | **Operational** |
| Persistent Agent Lab history | **Operational** |
| Consumer Probe foundations | **Operational / evolving** |

Current development is focused on external testing, broader observation coverage, richer catalogs, user experience, and distributed observation workflows.

See [`docs/roadmap.md`](docs/roadmap.md).

---

## Core principles

### Observer / SUT separation

DLLO does not allow the system under test to certify itself.

Observer-owned information includes:

- expected actions;
- expected tool selection;
- expected runtime propagation;
- recovery expectations;
- branch expectations;
- criterion evidence;
- verifier logic;
- PASS / FAIL verdicts.

The intended chain is:

```text
Task
  ↓
SUT execution
  ↓
Observer evidence collection
  ↓
Evaluation
```

not:

```text
SUT
  ↓
self-declared success
```

### No hidden selection

DLLO does not silently select:

- a global best model;
- a global best agent;
- the latest observation;
- a baseline;
- a candidate;
- a comparison pair;
- a geographic time threshold.

Selection remains explicit.

### Unknown remains unknown

Missing evidence is not converted into a negative claim.

```text
UNKNOWN != NOT_FEASIBLE
```

### Hard constraints stay hard

A hard constraint must not be silently relaxed.

Soft preferences may influence recommendations, but they never become blockers and never override hard constraints.

### Rejected comparisons remain visible

Pair discovery preserves both accepted and rejected pairs together with their comparability reasons.

---

## Temporal comparisons

A temporal comparison asks:

> What changed when a compatible target was observed again later from the same observation context?

Compatibility includes:

- same target;
- same benchmark suite;
- same suite version;
- compatible task coverage;
- complete required provenance;
- same observer identity;
- same observation region;
- candidate observation strictly after baseline.

DLLO reports observed changes without assigning unsupported causes.

---

## Geographic comparisons

A geographic comparison asks:

> What differences were observed from different regions under compatible benchmark conditions?

Compatibility includes:

- same target;
- same benchmark suite;
- same suite version;
- compatible task coverage;
- complete required provenance;
- different observation regions;
- observations sufficiently close in time.

The caller must explicitly provide the maximum accepted observation-time skew.

DLLO has **no hidden geographic skew threshold**.

---

## Observation pair discovery

DLLO can discover candidate temporal and geographic observation pairs.

Pair discovery:

- uses deterministic ordering;
- delegates comparability to canonical rules;
- preserves rejected pairs;
- records rejection reasons;
- does not automatically choose a baseline;
- does not automatically choose a candidate;
- does not use a magic `latest` observation.

Exact observation identifiers remain available for reproducible later comparison.

---

## Consumer Probe

DLLO also contains a Consumer Probe subsystem for measurements made through consumer-facing AI interfaces.

Its principles include:

- human-in-the-loop interaction;
- no automatic prompt submission;
- no scraping of private interfaces;
- no browser session-token or cookie collection;
- no private provider endpoints;
- no rate-limit bypass;
- local-first telemetry and history.

Consumer Probe records only what the observer can actually measure and preserves the distinction between observed client-side behavior and unknown provider infrastructure.

---

## Target taxonomy

DLLO distinguishes:

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

Compatibility is evaluated before workloads requiring unavailable capabilities are executed.

---

## Quickstart

DLLO requires **Python 3.10+**.

Clone the repository:

```bash
git clone https://github.com/ArckomVanDrike/distributed-llm-observatory.git
cd distributed-llm-observatory
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install DLLO and development dependencies:

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest -q
```

Run Ruff:

```bash
ruff check .
```


### Browser Public Preview

The browser interface requires Node.js and npm in addition to the Python setup above.

Start the local Agent Lab bridge from the repository root:

```bash
mkdir -p data/agent-runs

python -m observer.cli agent-lab-bridge \
  --observer-id local-observer \
  --region-code local \
  --history-root data/agent-runs
```

The bridge listens on `127.0.0.1:8766` by default.

In a second terminal, install the browser dependencies and start the development server:

```bash
cd web/collector
npm ci
npm run dev
```

Then open:

```text
http://127.0.0.1:5173/#/agent-lab/starter
```

The browser workflow exposes Agent Starter through the local bridge, including adaptive questioning, environment evidence, catalog-backed runtime selection, architecture assessment, and concrete stack recommendations.

To verify the browser-side implementation:

```bash
cd web/collector
npm test
npm run build
```

---

## Repository structure

```text
distributed-llm-observatory/
|
|-- analysis/          Analysis and statistical tooling
|-- benchmark/         Prompts, tasks, suites, and benchmark assets
|-- catalog/           Explicit Agent Starter catalog snapshots
|-- consumer_probe/    Consumer-interface observation subsystem
|-- docs/              Architecture, methodology, privacy, protocols
|-- judges/            Evaluation rubrics and validators
|-- observer/          Core observer and Agent Lab implementation
|-- pricing/           Pricing and economic measurement models
|-- schemas/           Shared structured data models
|-- server/            Service-side foundations
|-- tests/             Unit and integration tests
|-- web/collector/     Browser-side collector and Observatory UI
|
|-- README.md
|-- CONTRIBUTING.md
|-- LICENSE
`-- pyproject.toml
```

Execution, evidence, evaluation, storage, recommendation, and interpretation are intentionally separated.

---

## Documentation

Key documentation:

- [`docs/agent-starter-v1.md`](docs/agent-starter-v1.md) — Agent Starter v1 specification
- [`docs/architecture.md`](docs/architecture.md) — system architecture
- [`docs/methodology.md`](docs/methodology.md) — measurement methodology
- [`docs/observer-protocol.md`](docs/observer-protocol.md) — Observer and Agent Protocol
- [`docs/privacy.md`](docs/privacy.md) — privacy principles
- [`docs/quality-rubric.md`](docs/quality-rubric.md) — response-quality evaluation
- [`docs/roadmap.md`](docs/roadmap.md) — project roadmap
- [`benchmark/README.md`](benchmark/README.md) — benchmark organization

---

## What DLLO is not

DLLO is not:

- a provider leaderboard based on one global score;
- a system that automatically declares one model or agent globally “best”;
- a causal inference engine for undocumented provider infrastructure;
- an agent self-certification framework;
- a scraper for private consumer interfaces;
- a mechanism for bypassing provider restrictions.

DLLO is an **observation, evaluation, and agent-engineering framework**.

---

## Contributing

Contributions, testing, criticism, new benchmark ideas, and external observations are welcome.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting changes.

If you find a reproducibility problem, incorrect assumption, benchmark weakness, or questionable comparison rule, opening an issue is particularly valuable.

---

## License

Distributed LLM Observatory is released under the **MIT License**.

See [`LICENSE`](LICENSE).

---

## Core principle

> **Observe first. Compare carefully. Explain only when the evidence allows it.**
