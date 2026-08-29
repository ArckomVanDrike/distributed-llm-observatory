# DLLO Roadmap

Distributed LLM Observatory (**DLLO**) is being developed as an open-source framework for building agent configurations, testing real AI agents, and producing reproducible observations of AI-system behavior across time and observation regions.

This roadmap distinguishes between:

- capabilities already implemented and verified;
- work required for the public-preview experience;
- near-term technical expansion;
- longer-term distributed-observation goals.

The roadmap is intentionally not a promise of fixed release dates.

---

## Current milestone

The current repository is on the **0.1.x public-preview line**.

The principal v1 workflow foundations are now implemented:

```text
Build an agent
      |
      v
Agent Starter v1

Test an agent
      |
      v
Test Your Agent v1

Persist observations
      |
      v
History + qualification

Compare observations
      |
      v
Temporal / geographic Observatory
```

The immediate project focus has therefore shifted from core feature construction to:

```text
public packaging
documentation
user experience
external testing
broader observation coverage
```

---

# Completed

## Agent Protocol Core 1.0

**Status: Stable**

Agent Protocol Core 1.0 freezes the qualified behavioral protocol developed for agent evaluation.

Current coverage includes:

- exact output;
- instruction following;
- structured output;
- tool selection;
- ordered action sequences;
- runtime data propagation;
- failure handling and recovery;
- conditional branching;
- multi-branch decisions.

The protocol preserves the separation between:

```text
SUT execution
Observer evidence
Evaluation
```

The SUT cannot certify its own success.

---

## Test Your Agent v1

**Status: Complete**

The first complete Agent Lab testing workflow is implemented.

Current capabilities include:

- compatibility assessment;
- agent test sessions;
- local SUT protocol;
- observer-controlled task execution;
- action gateway;
- observer-owned evidence collection;
- technical evaluation;
- technical reports;
- persistent Agent Lab run artifacts;
- artifact loading and validation;
- historical session resolution.

Test Your Agent is designed to evaluate observable agent behavior rather than self-declared capability.

---

## Agent Starter v1

**Status: Complete**

Agent Starter v1 implements the full recommendation pipeline for helping users determine what kind of agent architecture and stack can reasonably satisfy their needs.

Supported goals:

- Coding;
- Knowledge / RAG;
- Automation;
- Voice;
- Personal assistant.

The pipeline includes:

```text
Intake
  |
  v
Adaptive questionnaire
  |
  v
Evidence + requirements
  |
  v
Requested capabilities
  |
  v
Candidate architectures
  |
  v
Technical feasibility
  |
  v
Decision assessment
  |
  v
Explicit catalog snapshot
  |
  v
Concrete stack resolution
  |
  v
Final report
```

Agent Starter v1 preserves:

- OBSERVED / DECLARED / DERIVED / UNKNOWN provenance;
- hard constraints;
- soft preferences;
- conservative UNKNOWN handling;
- architecture-before-model reasoning;
- explicit catalog snapshots;
- multiple valid recommendations;
- Why / Why Not explanations;
- no global hidden ranking.

---

## Adaptive Agent Starter questionnaire

**Status: Complete for v1 goals**

Goal-specific questioning is implemented for all five Agent Starter goals.

Cross-cutting and goal-specific areas currently include:

- offline requirements;
- source-code locality;
- knowledge-data locality;
- raw-audio locality;
- transcript locality;
- local-execution preference;
- filesystem access;
- test execution;
- RAG characteristics;
- citations and provenance;
- OCR;
- automation determinism;
- human approval;
- availability requirements;
- voice realtime interaction;
- interruption handling;
- persistent memory;
- proactive behavior;
- selective memory.

Questions are omitted when they cannot change the current decision or when the relevant user intent has already been explicitly established.

---

## Agent Starter catalog matching

**Status: Operational**

Agent Starter uses explicit catalog snapshots.

Current repository catalog:

```text
catalog/agent-starter/catalog-v0-1.json
```

The catalog currently contains a deliberately small set of model/runtime components suitable for validating the matching pipeline.

Catalog behavior preserves:

- explicit snapshot provenance;
- no hidden `latest`;
- no arbitrary first-match winner when multiple matches exist;
- visible zero-match outcomes;
- all candidate matches.

---

## Concrete stack resolution

**Status: Operational**

Agent Starter can translate architecture requirements into concrete catalog requirements and stack components.

Current stack families include requirements for:

- LLM components;
- coding capability;
- STT;
- TTS;
- runtime components where explicitly required.

Concrete stack resolution does not invent architectural properties that are not supported by candidate evidence.

---

## Agent Starter final report

**Status: Complete**

The final report exposes:

- evidence provenance;
- hard constraints;
- soft preferences;
- requested capabilities;
- candidate explanations;
- Why / Why Not;
- recommended architectures;
- recommended concrete stacks;
- possible alternatives;
- possible-but-not-recommended candidates;
- not-recommended candidates;
- explicit blockers.

Upgrade paths are not fabricated when the pipeline has no evidence source for them.

---

## Persistent Agent Lab history

**Status: Operational**

Agent Lab run artifacts can be persisted and inspected later.

History supports exact session resolution.

The implementation deliberately avoids:

- fuzzy UUID matching;
- UUID prefixes;
- implicit latest-run selection;
- hidden baseline selection.

---

## Observatory qualification

**Status: Operational**

A valid run artifact and an Observatory-qualified observation are intentionally different concepts.

Qualification is derived from artifact provenance.

Required provenance can include:

- observer identity;
- observation region;
- start time;
- target identity;
- suite identity;
- suite version;
- task coverage.

Legacy artifacts remain inspectable even when they do not qualify for newer Observatory comparisons.

---

## Temporal comparison

**Status: Operational**

DLLO can compare compatible observations of the same target across time.

Temporal comparison preserves:

- explicit baseline;
- explicit candidate;
- target compatibility;
- benchmark compatibility;
- suite-version compatibility;
- task-coverage compatibility;
- observer identity;
- observation region;
- temporal ordering.

The comparison describes observed change without assigning unsupported causes.

---

## Geographic comparison

**Status: Operational**

DLLO can compare compatible observations made from different observation regions.

Geographic comparison preserves:

- explicit observation regions;
- explicit baseline and candidate;
- benchmark compatibility;
- target compatibility;
- task-coverage compatibility;
- explicit maximum observation-time skew.

DLLO does not infer provider serving location from observer region.

There is no hidden geographic skew threshold.

---

## Observation pair discovery

**Status: Operational**

DLLO can discover candidate temporal and geographic comparison pairs from history.

Pair discovery:

- uses deterministic ordering;
- applies canonical comparability rules;
- preserves rejected pairs;
- records rejection reasons;
- does not choose an implicit winner;
- does not use a magic latest observation.

---

## Observatory Dashboard v1

**Status: Complete**

The browser layer contains an Observatory dashboard and supporting data flows for:

- Agent Lab history;
- temporal pair discovery;
- geographic pair discovery;
- temporal comparisons;
- geographic comparisons.

The dashboard communicates with canonical observer-owned comparison logic through the local bridge.

---

## Consumer Probe foundations

**Status: Operational / evolving**

Consumer Probe supports local-first measurement workflows for consumer-facing AI interfaces.

Current foundations include:

- manual human-in-the-loop workflows;
- scheduling;
- sampling;
- local telemetry;
- import;
- analytics;
- comparison;
- SQLite persistence;
- browser bridge.

Consumer Probe explicitly avoids:

- automatic prompt submission;
- private-interface scraping;
- browser session-token collection;
- cookie collection;
- private provider endpoints;
- rate-limit bypass.

---

## CLI

**Status: Operational**

The package installs the:

```text
dllo
```

command.

Current CLI families cover:

- benchmark execution;
- Consumer Probe;
- Agent Lab;
- Agent Lab history;
- Observatory summary;
- temporal comparison;
- geographic comparison;
- temporal pair discovery;
- geographic pair discovery.

---

## Automated verification

**Status: Operational**

The repository uses automated Python and browser-side tests to protect:

- protocol behavior;
- schema contracts;
- SUT / Observer boundaries;
- evidence semantics;
- comparison semantics;
- historical artifact behavior;
- Agent Starter decisions;
- catalog matching;
- concrete stack resolution;
- final reports;
- browser data flows.

The Agent Starter v1 completion milestone was merged to `main` with the complete repository test gate passing.

---

# Public Preview

The current development phase focuses on making the implemented system understandable and usable by people who did not build it.

## Documentation and repository packaging

**In progress**

Current work includes:

- public README;
- architecture documentation;
- roadmap;
- clearer Quickstart;
- repository metadata;
- screenshots;
- diagrams;
- release notes;
- external-user setup validation.

---

## Fresh-clone validation

**Planned for Public Preview**

DLLO should be tested from a clean environment using only public repository instructions.

The validation flow should cover:

```text
clone
  |
  v
install
  |
  v
run verification
  |
  v
start local interfaces
  |
  v
execute representative workflow
```

The objective is to find assumptions that are currently obvious only to repository developers.

---

## Public visual presentation

**Planned for Public Preview**

The project will receive a lightweight public presentation layer, including:

- real application screenshots;
- architecture visualization;
- workflow visualization;
- GitHub social preview;
- GitHub Pages landing page.

The public presentation must describe implemented behavior rather than mock future capabilities as current functionality.

---

## Agent Starter public interface

**Planned**

The Agent Starter v1 decision core is complete.

A dedicated user-facing interface remains to be exposed over the existing pipeline.

Potential interfaces include:

- browser workflow;
- CLI workflow;
- structured local API boundary.

The interface should preserve the same explicit evidence and decision semantics as the core pipeline.

---

## External testing

**Planned**

Public Preview should invite external users to:

- connect agents;
- run protocol tests;
- inspect reports;
- exercise Agent Starter;
- identify unclear setup instructions;
- challenge comparison rules;
- report reproducibility issues;
- propose benchmark cases.

External criticism of methodology and reproducibility is considered useful project input.

---

# Near-term expansion

## Richer Agent Starter catalog

The current Agent Starter catalog is intentionally small.

Near-term catalog work may include additional:

- LLMs;
- coding models;
- runtimes;
- STT systems;
- TTS systems;
- local execution options;
- cloud execution options;
- hardware/runtime compatibility metadata.

Catalog expansion must preserve explicit versioned snapshots.

---

## Richer candidate evidence

Additional candidate properties may enable more precise decisions around:

- offline operation;
- hardware fit;
- runtime requirements;
- execution locality;
- latency constraints;
- memory requirements;
- operational complexity.

Properties should remain explicit evidence rather than being inferred from architecture identifiers.

---

## Additional decision-active preferences

Agent Starter v1 intentionally activates only preferences with defensible decision semantics.

Future versions may add additional soft preferences when concrete cross-candidate evidence supports them.

Examples may include:

- operational simplicity;
- cost preference;
- latency preference;
- resource efficiency.

No preference should affect recommendations until its decision behavior is explicit and testable.

---

## Broader benchmark families

Agent Protocol Core 1.0 provides the stable current behavioral foundation.

Future benchmark families may extend coverage to new agent and AI-system capabilities while preserving versioned protocol contracts.

Possible areas include:

- richer browser interaction;
- longer-running workflows;
- multimodal behavior;
- collaborative agent workflows;
- stateful multi-session behavior;
- more complex failure recovery.

---

## Mobile workflows

Agent Starter and observation workflows should increasingly account for mobile devices.

Mobile support requires explicit handling of:

- restricted browser hardware visibility;
- mobile operating-system boundaries;
- app vs browser capability differences;
- microphone and camera access;
- local storage limits;
- runtime availability;
- power constraints.

Desktop assumptions should not silently become mobile assumptions.

---

## Observatory UX

The Observatory browser experience can expand around:

- observation exploration;
- clearer pair-selection workflows;
- provenance inspection;
- comparison visualization;
- rejected-pair explanations;
- historical navigation;
- export.

Visualization must not introduce interpretations that are absent from canonical comparison results.

---

# Distributed observation phase

The long-term value of DLLO depends on observations collected under reproducible conditions from multiple contexts.

## Distributed observers

Future work can enable independent observers to produce compatible observation artifacts.

The architecture should preserve:

```text
observer identity
region provenance
benchmark version
target identity
task coverage
time provenance
```

Distributed participation must not weaken reproducibility requirements.

---

## Shared observation datasets

A future public observation layer may aggregate qualified artifacts into shared datasets.

Potential capabilities include:

- public artifact publication;
- dataset snapshots;
- observation indexing;
- reproducible pair discovery;
- longitudinal analysis;
- cross-region analysis.

A centralized public service is not currently claimed by the repository.

---

## Public Observatory service

A future deployment may provide a public Observatory service built on the current artifact, qualification, history, and comparison contracts.

Such a service would require additional work around:

- ingestion;
- authentication where appropriate;
- artifact integrity;
- storage;
- indexing;
- abuse prevention;
- privacy;
- versioning;
- dataset governance;
- operational reliability.

The current `server/` package should therefore be treated as a foundation rather than an already-deployed public backend.

---

# Longer-term research directions

Potential research areas include:

- temporal behavior stability;
- cross-region observed variation;
- tool-use stability;
- retry and recovery behavior;
- human-intervention requirements;
- latency distributions;
- failure-rate changes;
- economic efficiency;
- agent architecture compatibility;
- reproducibility across independent observers.

These measurements may support hypotheses about underlying mechanisms.

DLLO should not convert those hypotheses into causal claims without independent evidence.

---

# Non-goals

The roadmap does not include turning DLLO into:

- a single global leaderboard;
- an automatic “best model” selector;
- an automatic “best agent” selector;
- an agent self-certification system;
- a provider infrastructure inference engine;
- a private-interface scraper;
- a rate-limit bypass system.

The Observatory is intended to preserve evidence and comparability rather than collapse heterogeneous systems into one score.

---

# Release philosophy

DLLO favors explicit, inspectable releases over hidden moving targets.

This applies to:

```text
protocol versions
benchmark suites
catalog snapshots
artifact schemas
comparison rules
```

A release should make it possible to determine which contracts produced an observation or recommendation.

---

## Current focus

The immediate sequence is:

```text
Public documentation
        |
        v
Repository presentation
        |
        v
Fresh-clone validation
        |
        v
Screenshots / visual assets
        |
        v
GitHub Pages
        |
        v
Public Preview release
        |
        v
External testing and observations
```

---

## Core principle

> **Observe first. Compare carefully. Explain only when the evidence allows it.**
