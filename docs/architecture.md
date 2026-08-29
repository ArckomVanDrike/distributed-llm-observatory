# DLLO Architecture

Distributed LLM Observatory (**DLLO**) is organized around a strict separation between execution, observation, evidence, evaluation, recommendation, persistence, and comparison.

The architecture supports three principal workflows:

```text
                         Distributed LLM Observatory
                                   |
             +---------------------+----------------------+
             |                     |                      |
             v                     v                      v
       Agent Starter         Test Your Agent         Observatory
             |                     |                      |
       What should I          Does the agent          What changed
          build?              behave correctly?        between runs?
```

These workflows share schemas, provenance rules, evidence semantics, and explicit decision boundaries, but they solve different problems.

---

## 1. System overview

At a high level:

```text
User / Observer
      |
      +------------------------------------------------------+
      |                                                      |
      v                                                      v
Agent Starter                                           Agent Lab
      |                                                      |
      |                                               Test Your Agent
      |                                                      |
      v                                                      v
Prepared evidence                                      Compatibility
      |                                                      |
      v                                                      v
Candidate architectures                                Test session
      |                                                      |
      v                                                      v
Technical feasibility                             Agent Protocol Core
      |                                                      |
      v                                                      v
Decision assessment                              Observer-owned evidence
      |                                                      |
      v                                                      v
Explicit catalog snapshot                              Evaluation
      |                                                      |
      v                                                      v
Concrete stack                                      Technical report
      |                                                      |
      v                                                      v
Final report                                      Persistent run artifact
                                                             |
                                                             v
                                                        Observatory
                                                             |
                                           +-----------------+-----------------+
                                           |                                   |
                                           v                                   v
                                      Temporal                           Geographic
                                      comparison                         comparison
```

DLLO does not collapse these stages into a single opaque score or decision.

Each layer has a specific responsibility.

---

## 2. Core architectural boundaries

Several boundaries are intentionally enforced throughout DLLO.

```text
System Under Test     != Observer
Execution             != Evidence
Evidence              != Evaluation
Technical feasibility != Recommendation
Run artifact          != Qualified observation
Observation           != Explanation
Local execution       != Offline capability
Privacy               != Connectivity
```

These distinctions are part of the project semantics rather than implementation details.

### System Under Test vs Observer

The system under test (**SUT**) receives what it needs to perform a task.

The observer owns:

- expected behavior;
- verifier-only information;
- evidence collection;
- evaluation criteria;
- PASS / FAIL decisions;
- comparison rules.

A SUT cannot certify its own success.

The intended execution chain is:

```text
Task
  |
  v
SUT execution
  |
  v
Observer evidence collection
  |
  v
Evaluation
```

not:

```text
SUT
  |
  v
Self-declared success
```

---

## 3. Agent Starter architecture

**Agent Starter v1** is the recommendation and agent-design workflow.

Its purpose is:

> Given what the user wants to build, their constraints, and capabilities that can actually be established, what agent architecture and concrete stack can reasonably be recommended, and why?

The current implementation lives primarily in:

```text
observer/core/agent_starter_*.py
schemas/agent_starter*.py
catalog/agent-starter/
```

### Unified pipeline

The end-to-end flow is:

```text
User intake
    |
    v
Input orchestration
    |
    v
Adaptive questionnaire
    |
    v
Prepared evidence + requirements
    |
    v
Requested capability projection
    |
    v
Candidate architecture generation
    |
    v
Technical feasibility
    |
    v
Candidate assessment
    |
    v
Plan construction
    |
    v
Explicit catalog snapshot matching
    |
    v
Concrete stack resolution
    |
    v
Recommendation classification
    |
    v
Final report + Why / Why Not
```

The unified pipeline is implemented by:

```text
observer/core/agent_starter_unified_pipeline.py
```

### Evidence provenance

Agent Starter distinguishes evidence provenance explicitly:

```text
OBSERVED
DECLARED
DERIVED
UNKNOWN
```

Missing information is not silently converted into a negative fact.

```text
UNKNOWN != NOT_FEASIBLE
```

### Constraints

Requirements are separated into:

```text
HARD constraints
SOFT preferences
```

Hard constraints cannot be silently relaxed.

Soft preferences can influence recommendation status but do not become blockers and cannot override hard constraints.

### Architecture before model

Agent Starter evaluates candidate architectures before selecting concrete catalog components.

The intended order is:

```text
USER GOAL
    |
    v
REQUIRED CAPABILITIES
    |
    v
HARD CONSTRAINTS
    |
    v
OBSERVED ENVIRONMENT
    |
    v
TECHNICAL FEASIBILITY
    |
    v
SOFT PREFERENCES
    |
    v
OPERATIONAL FIT
    |
    v
CATALOG MATCHING
    |
    v
RECOMMENDATION
```

Concrete products or models are therefore not used as a substitute for architecture reasoning.

### Explicit catalogs

Agent Starter catalog snapshots live under:

```text
catalog/agent-starter/
```

Catalog resolution is explicit.

There is no hidden `latest` catalog.

A catalog snapshot becomes part of the provenance of the resulting recommendation.

### No hidden winner

Recommendation states are explicit and can preserve multiple valid architectures:

```text
RECOMMENDED
POSSIBLE
POSSIBLE_BUT_NOT_RECOMMENDED
NOT_RECOMMENDED
```

Multiple `RECOMMENDED` candidates are allowed when the evidence does not justify choosing a unique winner.

DLLO does not introduce an implicit global score or tie-break.

### Current interface boundary

Agent Starter v1 is currently implemented as a Python core pipeline and schema layer.

Its complete decision engine is part of the repository, but a dedicated public Agent Starter CLI or browser workflow is not yet exposed as a separate product interface.

This distinction is intentional in the current public-preview architecture.

---

## 4. Test Your Agent architecture

**Test Your Agent v1** evaluates real agent behavior through an observer-controlled protocol.

Principal implementation areas include:

```text
observer/core/agent_test_session_runner.py
observer/core/agent_lab_protocol_runner.py
observer/core/action_gateway.py
observer/core/action_task_environment.py
observer/core/agent_technical_report.py
observer/agent_lab_bridge.py
schemas/agent_lab.py
schemas/sut_protocol.py
```

The flow is:

```text
Agent
  |
  v
Compatibility assessment
  |
  v
Agent test session
  |
  v
Protocol runner
  |
  v
Task environment / action gateway
  |
  v
Observed behavior
  |
  v
Observer-owned evidence
  |
  v
Evaluation
  |
  v
Technical report
  |
  v
Persistent Agent Lab run artifact
```

---

## 5. Agent Protocol Core

**Agent Protocol Core 1.0** defines the stable behavioral evaluation contract used by Test Your Agent.

The protocol currently covers:

```text
exact output
instruction following
structured output
tool selection
ordered action sequences
runtime data propagation
failure recovery
conditional branching
multi-branch decisions
```

Protocol execution is deliberately separated from verifier-owned expectations.

The observer controls benchmark fixtures and evaluation logic.

---

## 6. Local SUT protocol

DLLO can communicate with an agent through a local HTTP SUT adapter.

The reference protocol exposes:

```text
GET  /v1/manifest
POST /v1/execute
```

The observer-side local HTTP adapter uses these endpoints to inspect the public SUT manifest and request execution.

For tool-mediated tasks, the observer action gateway exposes tool operations using routes shaped as:

```text
/v1/tools/{tool}
```

This local protocol allows real agent behavior to be exercised without exposing observer-only expectations to the agent.

---

## 7. Agent Lab bridge

The browser-facing Agent Lab experience communicates with the Python observer through a local bridge.

Current Agent Lab / Observatory bridge routes include:

```text
GET  /v1/agent-tests

GET  /v1/agent-observation-pairs/temporal
GET  /v1/agent-observation-pairs/geographic

POST /v1/agent-comparisons/temporal
POST /v1/agent-comparisons/geographic
```

The bridge is implemented in:

```text
observer/agent_lab_bridge.py
```

This bridge is a local application boundary.

It should not be confused with a centralized public Observatory backend.

---

## 8. Persistent history and run artifacts

Agent Lab test results can be represented as persistent run artifacts.

A run artifact preserves the evidence and provenance required to inspect an execution later.

History supports exact observation and session resolution.

DLLO intentionally avoids fuzzy historical selection mechanisms such as:

```text
latest
best
recent enough
UUID prefix
implicit baseline
```

Exact identifiers remain the basis for reproducible historical resolution.

---

## 9. Observatory architecture

The Observatory operates on completed run artifacts.

Not every valid artifact is automatically a qualified Observatory observation.

```text
Valid run artifact
        |
        v
Observation qualification
        |
        +---------- rejected / insufficient provenance
        |
        v
Qualified observation
        |
        v
History
        |
        v
Pair discovery
        |
        v
Explicit pair selection
        |
        +--------------------------+
        |                          |
        v                          v
Temporal comparison       Geographic comparison
```

Qualification is derived from artifact provenance rather than accepted as a self-declared property.

Typical provenance includes:

```text
observer identity
observation region
start time
target identity
suite identity
suite version
task coverage
```

---

## 10. Temporal comparison

Temporal comparison asks:

> What changed when a compatible target was observed again later from the same observation context?

Comparability requires compatible target, benchmark, version, task coverage, observer identity, region, provenance, and temporal ordering.

The result reports observed differences.

It does not assign an unsupported cause.

There is no automatic baseline or candidate selection.

---

## 11. Geographic comparison

Geographic comparison asks:

> What differences were observed from different regions under compatible benchmark conditions?

The observation region represents where the observation originated.

It does not represent an inferred provider serving location.

```text
Observed from CL-Los-Lagos
```

does not imply:

```text
Served from Chile
```

Geographic comparisons also require an explicit maximum observation-time skew.

There is no hidden global skew threshold.

---

## 12. Observation pair discovery

Pair discovery searches history for potential temporal or geographic comparisons.

Its responsibilities are:

```text
history
  |
  v
candidate pair generation
  |
  v
canonical comparability rules
  |
  +---------- rejected pair + reason
  |
  v
comparable pair
```

Rejected pairs remain visible.

Pair discovery does not automatically choose which pair the user should compare.

This preserves reproducibility and avoids hidden selection logic.

---

## 13. Web collector and Observatory UI

The browser application lives under:

```text
web/collector/
```

It is currently built with:

```text
TypeScript
Vite
Vitest
```

The web layer contains dedicated components for:

```text
Agent Lab
Agent Test
Agent Test history
Agent Test comparison
Observatory dashboard
Observatory pair discovery
Consumer collection
Navigation and application shell
```

The browser calls explicit local bridge endpoints rather than reproducing canonical comparison logic independently.

The Python observer remains the authoritative layer for qualification and comparison semantics.

---

## 14. Consumer Probe architecture

Consumer Probe is a separate observation path for consumer-facing AI interfaces.

It includes components for:

```text
local collection
sampling
scheduling
import
local telemetry
analytics
comparison
SQLite persistence
browser bridge
```

Its constraints include:

```text
human-in-the-loop
no automatic prompt submission
no private-interface scraping
no browser session-token collection
no cookie collection
no private provider endpoints
no rate-limit bypass
```

Consumer Probe distinguishes locally observable client behavior from unknown provider-side behavior.

---

## 15. CLI layer

The installed package exposes:

```text
dllo
```

through:

```text
observer.cli:main
```

Current CLI areas include benchmark execution, Consumer Probe workflows, Agent Lab execution, history, Observatory summaries, pair discovery, and comparisons.

Examples of current command families include:

```text
consumer-import
consumer-summary
consumer-detect
consumer-schedule
consumer-next
consumer-bridge

agent-lab-bridge
agent-test
agent-compare
agent-compare-temporal
agent-compare-temporal-history
agent-compare-geographic
agent-compare-geographic-history
agent-observatory-summary
agent-history
agent-pairs-temporal
agent-pairs-geographic
```

The CLI is one interface over the same observer-owned core semantics.

---

## 16. Schema layer

Shared structured contracts live under:

```text
schemas/
```

Current schema families include:

```text
Agent Lab
Agent Starter
Agent Starter catalog
Agent Starter questionnaire
Agent Starter report
Agent Starter stack
benchmark
compatibility
evaluation
fixture
hardware
model profile
observation
pricing
record
SUT protocol
target
```

Schemas define boundaries between components and protect serialized behavior from informal coupling.

Where possible, decisions and artifacts cross subsystem boundaries through explicit structured contracts rather than arbitrary dictionaries.

---

## 17. Repository organization

The principal repository areas are:

```text
analysis/
    analysis and statistical tooling

benchmark/
    benchmark documentation and assets

catalog/
    explicit versioned Agent Starter catalog snapshots

consumer_probe/
    consumer-interface observation subsystem

docs/
    architecture, methodology, privacy and protocol documentation

judges/
    evaluation rubrics and validators

observer/
    observer runtime, Agent Lab, Agent Starter and CLI

schemas/
    shared structured contracts

server/
    service-side foundation only

tests/
    unit and integration verification

web/collector/
    browser collector, Agent Lab and Observatory UI
```

---

## 18. Current deployment boundary

DLLO currently provides the architecture required to create, persist, qualify, discover, and compare observations.

It also provides a local browser-to-observer bridge and a local SUT protocol.

The repository does **not** currently claim to operate a centralized global Observatory service or a large public distributed observer network.

In particular:

```text
server/
```

currently represents service-side foundations rather than a production public backend.

The distinction matters:

```text
Distributed-observation architecture
                !=
Already-deployed global observation network
```

Large-scale distributed collection and public coordination remain future deployment layers built on top of the current observer, provenance, qualification, and comparison contracts.

---

## 19. Design invariants

The following invariants should remain true as DLLO evolves:

```text
No SUT self-certification.

No hidden latest observation.

No automatic baseline or candidate.

No global agent/model score.

No hidden geographic skew threshold.

No inferred serving location.

No unsupported causal inference.

Rejected comparison pairs remain visible.

Legacy artifacts remain inspectable.

UNKNOWN does not become NOT_FEASIBLE.

Hard constraints are not silently relaxed.

Soft preferences do not become blockers.

Architecture reasoning precedes catalog selection.

Candidate properties are explicit evidence.

Local execution does not imply offline capability.

Privacy does not imply offline capability.

Multiple valid recommendations may remain unresolved.

Observatory comparisons answer:
"What changed?"

They do not automatically answer:
"Why?"
```

These invariants are part of DLLO's scientific and engineering contract.

---

## 20. Architectural direction

The current architecture has reached a complete v1 loop for the principal Agent Lab workflows:

```text
Agent Starter
      |
      v
Architecture / stack recommendation

Test Your Agent
      |
      v
Observed execution + evidence

Persistent history
      |
      v
Qualified observations

Pair discovery
      |
      v
Explicit comparison

Observatory
      |
      v
Reproducible observed change
```

Future work can expand interfaces, catalogs, datasets, observer coordination, and public deployment without weakening the evidence and comparison semantics underneath them.

---

## Core principle

> **Observe first. Compare carefully. Explain only when the evidence allows it.**
