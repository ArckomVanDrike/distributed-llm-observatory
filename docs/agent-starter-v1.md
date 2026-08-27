# Agent Starter v1

## Status

Design specification.

This document defines the functional and decision-making contract for
Agent Starter v1 before implementation.

Agent Starter must remain deterministic, explainable, evidence-aware,
and separate technical feasibility from product recommendation.

---

## 1. Mission

Agent Starter answers:

> Given what the user wants to build, their constraints, and the
> capabilities we can actually observe, what concrete agent architecture
> and stack should they use, and why?

Agent Starter is not only a hardware compatibility checker.

It combines:

- user goals;
- declared constraints;
- observed device capabilities;
- derived capability requirements;
- unknown information;
- compatibility evidence;
- curated recommendation catalog data.

The result must explain both:

- what can technically run;
- what is actually sensible to use.

---

## 2. Core principle

Technical feasibility is not the same as recommendation.

A configuration may be technically possible while still being a poor
choice for the user's stated goal.

Agent Starter must therefore evaluate these independently.

### Technical feasibility

- `feasible`
- `limited`
- `not_feasible`
- `unknown`

### Recommendation

- `recommended`
- `possible`
- `possible_but_not_recommended`
- `not_recommended`

Example:

    Technical feasibility:
    FEASIBLE

    Recommendation:
    POSSIBLE, BUT NOT RECOMMENDED

This distinction is mandatory throughout Agent Starter.

---

## 3. Primary user goals

Agent Starter v1 supports five primary goals.

### Personal Assistant

Conversation, memory, personal knowledge, tasks, calendar, email,
documents, and related personal workflows.

### Knowledge / RAG Agent

Document question answering, private knowledge bases, research
collections, retrieval, citations, and knowledge that may change over
time.

### Coding Agent

Coding assistance, repository understanding, repository modification,
test execution, Git usage, shell tools, and controlled autonomous coding.

### Automation Agent

Browser automation, APIs, email, filesystem, databases, applications,
scheduled workflows, and multi-step automation.

### Voice Agent

Speech input, speech output, conversational voice, realtime interaction,
voice automation, and hybrid speech pipelines.

---

## 4. Private / Offline is not a sixth primary goal

Privacy and offline operation are cross-cutting constraints.

Examples include:

- private coding agent;
- offline knowledge agent;
- private voice agent;
- offline personal assistant;
- private automation agent.

Agent Starter must model privacy and connectivity separately.

`private != offline`

A system may be:

- private but online;
- offline but not particularly private;
- private and offline;
- neither.

---

## 5. Evidence provenance

Every decision-relevant input must retain provenance.

### OBSERVED

DLLO directly observed or measured the value.

Examples:

- operating system;
- available memory;
- logical CPU count;
- accelerator information when available;
- microphone availability;
- runtime availability.

### DECLARED

The user explicitly provided the value or requirement.

Examples:

- source code must remain local;
- offline operation is required;
- monthly budget is free-only;
- realtime voice is required.

### DERIVED

The requirement follows deterministically from another user choice.

Example:

    User selected:
    "Modify files and run tests"

    Derived capabilities:
    filesystem_read
    filesystem_write
    shell_execution
    test_execution

### UNKNOWN

There is insufficient evidence.

Unknown must never be silently converted into a positive or negative
claim.

In particular:

    UNKNOWN != NOT_FEASIBLE

---

## 6. Existing DLLO foundation

Agent Starter should reuse the existing DLLO foundation where
appropriate.

### HardwareProfile

Existing hardware schema provides:

- device class;
- profile source;
- operating system;
- architecture;
- CPU model;
- logical CPU count;
- total memory;
- accelerator information;
- collection limitations.

Supported profile sources already include:

- native;
- browser-limited;
- manual.

Agent Starter must not create a competing hardware profile model unless
a future requirement cannot be represented by the existing schema.

### ModelProfile

The existing technical model profile provides:

- model identifier;
- parameter count;
- quantization;
- context window;
- runtime;
- execution location.

It should remain a lightweight technical profile.

Recommendation catalog metadata should not automatically be added to
ModelProfile.

### CompatibilityAssessment

The existing compatibility estimator is evidence for Agent Starter.

It currently estimates local model memory suitability from:

- total device memory;
- parameter count;
- quantization;
- conservative fixed weight overhead.

Its current verdicts are not the same thing as the final Agent Starter
recommendation.

Agent Starter consumes compatibility assessments as evidence.

---

## 7. Hard constraints and soft preferences

Agent Starter must distinguish between hard constraints and soft
preferences.

### Hard constraint

Must not be violated.

Examples:

- source code cannot leave the environment;
- runtime must work offline;
- paid services are forbidden;
- raw audio cannot leave the device.

### Soft preference

May be traded off, but only explicitly.

Examples:

- cloud should preferably be avoided;
- lower cost preferred;
- simplest setup preferred;
- lower latency preferred.

Soft preferences must never override hard constraints.

---

## 8. Decision order

Agent Starter should evaluate decisions in this conceptual order:

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

---

## 9. Common questions

Only questions capable of changing a decision belong in v1.

Common topics include:

- where the agent may run;
- what data must stay local;
- what must work offline;
- how frequently offline operation matters;
- whether degraded offline capability is acceptable;
- monthly budget;
- latency sensitivity;
- expected number of users;
- availability requirements;
- preferred setup complexity.

Agent Starter should not ask the user for values that DLLO can reliably
observe.

---

## 10. Adaptive goal questions

### Coding

Relevant topics include:

- coding assistant vs repository assistant vs coding agent vs autonomous
  coding agent;
- whether source code may leave the environment;
- repository size;
- programming languages;
- filesystem access;
- shell access;
- test execution;
- Git;
- permitted autonomy;
- execution isolation.

### Knowledge / RAG

Relevant topics include:

- corpus size;
- document types;
- scanned documents;
- privacy boundary;
- citations;
- update frequency;
- lexical vs semantic search requirements;
- languages;
- concurrency.

Agent Starter must be able to conclude that full RAG is unnecessary for
very small corpora.

### Voice

Relevant topics include:

- simple voice Q&A vs natural conversation vs realtime;
- microphone or uploaded audio;
- speech output;
- raw-audio privacy;
- transcript privacy;
- languages;
- natural speech requirement;
- interruptions / barge-in;
- push-to-talk, wake word, or continuous listening.

Voice recommendations must consider end-to-end pipeline latency, not only
whether each component can run individually.

### Automation

Relevant topics include:

- systems/tools involved;
- read vs write vs destructive access;
- autonomy;
- approval policy;
- irreversible actions;
- financial/legal/account impact;
- execution frequency;
- 24/7 availability;
- integrations;
- credentials;
- retry/recovery requirements.

Agent Starter must be able to recommend traditional automation instead
of an AI agent when the workflow is deterministic.

### Personal Assistant

Relevant topics include:

- conversation;
- persistent memory;
- personal knowledge;
- calendar/tasks/email;
- proactive behavior;
- memory retention;
- what should be remembered;
- what must not be remembered;
- tool access;
- availability.

Agent Starter must not assume that storing all conversation history is
a sensible memory architecture.

---

## 11. Privacy boundaries

Privacy must be modeled per data class when needed.

Example:

    source_code       LOCAL_ONLY
    raw_audio         LOCAL_ONLY
    transcript        REMOTE_ALLOWED
    personal_memory   LOCAL_ONLY
    public_web_data   REMOTE_ALLOWED

Candidate components must be checked against the data they receive and
where processing occurs.

Possible boundary classes:

- local-only;
- user-controlled environment;
- private/local network;
- remote allowed;
- unknown.

---

## 12. Offline boundaries

Offline requirements may also apply per capability.

Examples:

- inference must work offline;
- documents must remain searchable offline;
- voice must work offline;
- web search may require network access.

Agent Starter may recommend degraded-mode architectures.

Example:

    ONLINE
    hosted model
    web search
    remote tools

    OFFLINE FALLBACK
    lightweight local model
    local documents
    local tools

---

## 13. Candidate architectures

Agent Starter may evaluate architectures such as:

- local-first;
- cloud-first;
- hybrid;
- device-local;
- user-controlled server;
- always-on server;
- edge/mobile;
- direct-context;
- local RAG;
- hybrid RAG;
- cloud/server RAG;
- local voice pipeline;
- hybrid voice pipeline;
- cloud voice pipeline;
- traditional automation;
- supervised automation agent;
- autonomous workflow agent.

Architecture is selected before a concrete model.

---

## 14. Technical feasibility

Technical feasibility answers:

> Can this candidate realistically operate in the known environment?

Possible values:

### FEASIBLE

Known evidence supports the configuration.

### LIMITED

The configuration may operate, but one or more technical constraints
provide limited headroom or degraded capability.

### NOT_FEASIBLE

A required capability or hard technical requirement is known to be
unsatisfied.

### UNKNOWN

Critical information is unavailable.

Unknown information should reduce confidence rather than become a
negative assumption.

---

## 15. Recommendation

Recommendation answers:

> Given the user's actual goal and constraints, should this candidate be
> used?

### RECOMMENDED

Best current fit among evaluated candidates.

### POSSIBLE

A sensible alternative with explicit trade-offs.

### POSSIBLE_BUT_NOT_RECOMMENDED

Technically possible, but not a sensible choice for the stated goal.

Agent Starter must explain this explicitly.

Example:

    This configuration can run on your device,
    but it is not the most sensible choice for your stated goal.

### NOT_RECOMMENDED

Conflicts strongly with the intended workload, constraints, operating
model, or risk profile.

---

## 16. Constraint conflict

Agent Starter must detect when no candidate satisfies all hard
requirements.

Example:

    Goal:
    realtime fully local voice

    Device:
    severely constrained

    Cloud:
    forbidden

    Hardware upgrade:
    unavailable

Output:

    CONSTRAINT CONFLICT

    No current candidate satisfies all declared requirements.

Agent Starter must not silently relax a constraint.

Instead it may present explicit alternatives:

- reduce capability;
- upgrade hardware;
- use another user-controlled device/server;
- allow selected remote processing;
- change availability or latency expectations.

---

## 17. Operational sensibility

Technical operation alone is insufficient.

Examples:

### Availability

A laptop-hosted automation may be technically feasible but not
recommended for a 24/7 requirement.

### Latency

A CPU-only local voice pipeline may technically run but be unsuitable
for requested realtime conversation.

### Complexity

A full agent framework may be technically valid but unnecessary for a
deterministic task.

### Cost

A paid architecture may be valid but unnecessary when an equivalent
free/local candidate satisfies all requirements.

---

## 18. AI necessity

Agent Starter must be allowed to recommend not using an AI agent.

Example deterministic workflow:

    fetch API
    save result
    send fixed message

Recommended:

    conventional automation

Possible but not recommended:

    LLM-based autonomous agent

Reason:

- no semantic interpretation required;
- no dynamic planning required;
- additional cost, latency, and failure modes.

---

## 19. Goal-specific decision principles

### Coding

- repository read requires filesystem read;
- code modification requires filesystem write;
- test execution requires shell/runtime access;
- autonomous coding strongly favors isolation and recovery;
- large repositories favor indexing/retrieval;
- source-code privacy may exclude cloud inference.

### RAG

- very small corpora may not require RAG;
- medium/large corpora favor retrieval;
- scans require OCR;
- citations require source provenance;
- exact identifiers may favor lexical/hybrid retrieval;
- frequent updates favor incremental indexing.

### Voice

- uploaded audio does not automatically require streaming;
- realtime interaction favors streaming components;
- raw-audio local-only excludes remote STT;
- transcript remote-allowed may permit a hybrid architecture;
- interruptions require turn management / VAD;
- end-to-end latency determines operational fit.

### Automation

- deterministic workflows may not need AI;
- external writes require approval analysis;
- irreversible/high-impact actions favor human approval;
- idempotent operations may support safe retry;
- blind retry of non-idempotent actions is not recommended;
- 24/7 operation requires an always-available deployment.

### Personal Assistant

- no cross-session memory means persistent memory may be unnecessary;
- selective memory favors structured storage;
- persistent memory should support inspection/edit/delete;
- retaining everything indefinitely may be feasible but not recommended;
- proactive behavior requires scheduling/background execution.

---

## 20. Recommendation confidence

Recommendation confidence reflects evidence completeness.

It does not represent global model quality.

### HIGH

Critical inputs are observed, declared, or reliably derived.

### MEDIUM

Some meaningful factors remain unknown.

### LIMITED

One or more critical feasibility factors are unknown.

Example:

    Recommendation:
    local-first

    Confidence:
    LIMITED

    Reason:
    exact accelerator memory could not be observed.

---

## 21. Recommendation Catalog

The decision engine and catalog are separate systems.

The decision engine asks for properties.

Example:

    coding-capable
    local
    tool use
    resource band X
    free-only

The catalog returns current candidates.

Agent Starter must not encode rules such as:

    if RAM == 16 GB:
        recommend model X

The catalog should eventually cover:

- LLMs;
- runtimes;
- agent frameworks;
- embedding models;
- vector stores;
- STT;
- TTS;
- supporting tools.

Catalog entries must retain provenance and freshness metadata.

Expected metadata includes:

- identifier;
- vendor;
- family;
- model/tool version;
- capabilities;
- deployment modes;
- resource profile;
- supported runtimes;
- context characteristics;
- language support;
- streaming support where relevant;
- license;
- pricing class;
- privacy implications;
- sources;
- verified-at timestamp.

---

## 22. Candidate evaluation

A candidate should retain multidimensional evidence rather than a single
global score.

Example:

    Hardware fit       STRONG
    Privacy fit        STRONG
    Capability fit     STRONG
    Latency fit        MODERATE
    Cost fit           STRONG

    Technical feasibility
    FEASIBLE

    Recommendation
    RECOMMENDED

Agent Starter should not produce a universal numerical ranking such as:

    Model A: 87
    Model B: 84

---

## 23. Why / Why not

Explanations must derive from decision evidence.

Example:

    WHY THIS ARCHITECTURE

    ✓ documents remain local
      source: declared privacy boundary

    ✓ local retrieval fits the observed device
      source: observed hardware profile

    ✓ cloud inference is permitted
      source: declared constraint

    ✓ corpus size benefits from retrieval
      source: derived requirement

The same evidence should support rejection explanations.

---

## 24. Final report

Agent Starter v1 should produce a report containing at least:

- user goal;
- requested capabilities;
- observed evidence;
- declared evidence;
- derived evidence;
- unknown evidence;
- hard constraints;
- soft preferences;
- candidate architectures;
- rejected architectures and reasons;
- technical feasibility;
- recommendation verdict;
- confidence;
- recommended architecture;
- concrete recommended stack;
- alternative stack;
- possible-but-not-recommended options;
- blockers;
- upgrade paths;
- catalog snapshot/freshness information.

Example:

    YOUR AGENT STARTER PLAN

    Goal
    Private coding agent

    Recommended architecture
    LOCAL-FIRST

    Technical feasibility
    FEASIBLE

    Recommendation
    RECOMMENDED

    Confidence
    HIGH

    Why
    ✓ source code must remain local
    ✓ local hardware fit is adequate
    ✓ filesystem and shell execution are required

    Recommended stack
    Model: ...
    Runtime: ...
    Agent layer: ...
    Tools: ...
    Deployment: ...

    Alternative
    ...

    Possible, but not recommended
    ...

    Next step
    Build → Test Your Agent

---

## 25. Golden decision fixtures

Before implementation, Agent Starter should define deterministic fixture
scenarios covering at least:

1. Local private coding agent on adequate hardware.
2. CPU-only coding agent where cloud is allowed.
3. CPU-only coding agent where code cannot leave the device.
4. Tiny document collection where full RAG is unnecessary.
5. Private medium RAG on capable hardware.
6. Large multi-user RAG on weak local hardware with cloud allowed.
7. Realtime offline voice on constrained hardware.
8. Hybrid voice where raw audio stays local but transcript may leave.
9. Deterministic workflow where an AI agent is unnecessary.
10. Supervised email automation where autonomous send is not recommended.
11. 24/7 automation requested on a laptop that is not always available.
12. Personal assistant with selective persistent memory.
13. Personal assistant where indefinite storage of all conversations is
    unnecessary.
14. Mobile/browser environment with important hardware information
    unknown.
15. Hard constraint conflict with no satisfying candidate.

These fixtures should later become automated tests.

---

## 26. Out of scope for v1

Agent Starter v1 does not include:

- GitHub Repository Scout;
- GitHub scraping;
- automated transformer training;
- automated fine-tuning;
- automatic software installation;
- automatic Docker provisioning;
- cloud account provisioning;
- subscription purchases;
- deployment automation;
- large uncurated model catalogs;
- opaque LLM-based recommendation logic;
- universal model rankings;
- global recommendation scores.

Repository discovery belongs to a later phase after the recommendation
engine is stable.

---

## 27. v1 definition of done

Agent Starter v1 is complete when each supported primary goal can produce
a deterministic recommendation from:

    USER NEED
        +
    DECLARED CONSTRAINTS
        +
    OBSERVED DEVICE EVIDENCE
        +
    DERIVED REQUIREMENTS
        +
    UNKNOWN FACTORS
        ↓
    CANDIDATE ARCHITECTURES
        ↓
    TECHNICAL FEASIBILITY
        ↓
    RECOMMENDATION
        ↓
    CONCRETE STACK
        +
    ALTERNATIVE
        +
    WHY / WHY NOT

The recommendation must remain reproducible and explainable from the
recorded evidence.
