# DLLO Privacy

Distributed LLM Observatory (**DLLO**) is designed around data minimization, explicit provenance, and local-first observation workflows.

The project collects information only when it is required to support:

- execution;
- evaluation;
- reproducibility;
- technical compatibility;
- explicit comparison;
- user-requested recommendation.

DLLO does not treat access to an AI interface, local device, or connected agent as permission to collect unrelated information.

---

## 1. Privacy model

DLLO distinguishes several concepts that are often incorrectly combined:

```text
privacy
connectivity
execution locality
offline capability
observation provenance
```

They are not interchangeable.

For example:

```text
private != offline

local execution != offline capability

observer region != provider serving location
```

A system may execute locally while still requiring network access.

A system may operate offline while still handling data in ways the user considers unacceptable.

These properties are modeled independently.

---

## 2. Local-first design

Consumer Probe is designed as a local-first measurement subsystem.

Current local workflows use:

```text
browser extension storage
local observer processes
local SQLite history
localhost bridges
```

where applicable.

Local collection is preferred over unnecessary transmission.

The presence of locally collected information does not automatically imply permission to publish or share it.

---

## 3. Consumer Probe

Consumer Probe measures behavior visible from the user-side environment.

It can record information such as:

- probe identifiers;
- observation timestamps;
- platform metadata;
- measurement outcomes;
- local timing information;
- browser-related local telemetry;
- collector provenance;
- schedule provenance;
- locally captured response information when configured.

Consumer Probe is intentionally **human-in-the-loop**.

It is not intended to automate private consumer-interface interaction.

---

## 4. Local telemetry

Consumer Probe can collect local browser and host telemetry when supported by the operating system.

Current telemetry includes fields such as:

```text
browser process count
browser RSS memory
browser PSS memory when available
browser CPU usage
telemetry timestamps
collector version
browser scope
```

These measurements describe the local client environment.

They do not provide visibility into undocumented provider infrastructure.

For example:

```text
high local browser CPU
```

does not establish:

```text
provider-side computational load
```

---

## 5. Telemetry availability

Local telemetry is capability-dependent.

Some measurements may be unavailable because of:

- operating-system restrictions;
- browser sandboxing;
- permissions;
- platform differences;
- unavailable local telemetry sources.

Failure to collect a telemetry field should remain explicit.

Missing telemetry should not be fabricated or inferred.

---

## 6. Browser process telemetry

Where supported, the local telemetry collector can inspect the browser process tree to estimate browser-resource consumption.

Current measurements include:

```text
process count
RSS
PSS when available
CPU
```

This information is used to characterize the **local observation environment**.

It must not be interpreted as provider-side resource consumption.

---

## 7. Response text

Consumer Probe distinguishes between local capture and data that may leave the local machine.

The externally shareable representation is intentionally separate from the complete local record.

Response text is removed from that representation unless the applicable capture and sharing conditions explicitly permit it.

Conceptually:

```text
local record
    |
    v
sharing policy
    |
    +---- response sharing not permitted
    |             |
    |             v
    |      response text removed
    |
    v
shareable representation
```

Local capture therefore does not automatically imply external sharing.

---

## 8. Browser extension storage

The Consumer Probe browser extension uses browser-local storage for its local history and state.

This supports:

- local samples;
- local history;
- local measurement state;
- interaction with the localhost observer bridge.

Browser-local storage should not be interpreted as a cloud synchronization mechanism controlled by DLLO.

Actual browser behavior may depend on the browser implementation and user configuration.

---

## 9. Session credentials and cookies

Consumer Probe is not designed to collect provider authentication material.

Project policy explicitly excludes collection of:

```text
browser session tokens
provider cookies
private authentication state
```

DLLO measurement workflows should not require users to export or expose provider session credentials.

---

## 10. Private provider interfaces

DLLO does not rely on undocumented private provider endpoints as part of the Consumer Probe methodology.

Consumer Probe should not become a mechanism for:

- private API discovery;
- private endpoint invocation;
- authentication bypass;
- session extraction;
- provider-interface scraping.

Observations should remain grounded in legitimate user-visible interaction and supported local measurement.

---

## 11. No rate-limit bypass

DLLO is not designed to bypass provider rate limits or usage restrictions.

Measurement methodology must operate within the normal access conditions available to the user.

A benchmark or observation workflow should not introduce evasion mechanisms merely to increase measurement volume.

---

## 12. Human-in-the-loop interaction

Consumer-facing observation remains human-controlled.

The system should not silently submit prompts on the user's behalf through private consumer interfaces.

The human observer remains responsible for initiating the consumer-interface interaction.

This boundary reduces both privacy risk and methodological ambiguity.

---

## 13. Agent Lab

Test Your Agent processes data required to execute and evaluate explicit benchmark tasks.

Relevant information can include:

- target manifest;
- declared target capabilities;
- session identifier;
- observer identifier;
- observation region;
- execution timestamps;
- task inputs;
- observed outputs;
- observed tool actions;
- runtime evidence;
- evaluation evidence;
- technical reports.

The SUT receives only the public execution contract necessary for the task.

Verifier-only expectations remain observer-owned.

---

## 14. SUT / Observer privacy boundary

Separating the SUT from observer-owned information is also a data-boundary decision.

The SUT should not receive:

- expected action sequences;
- verifier logic;
- configured evaluation verdicts;
- private observer expectations;
- comparison conclusions;

unless the protocol explicitly requires some value to become visible through normal runtime interaction.

This protects both benchmark integrity and information minimization.

---

## 15. Local SUT protocol

DLLO currently supports a local HTTP protocol for testing agents.

Principal SUT routes include:

```text
/v1/manifest
/v1/execute
```

Tool-mediated execution may also use observer-controlled local action-gateway routes.

The local protocol is intended to expose only the information necessary for execution.

It is not a remote public ingestion API.

---

## 16. Agent Lab artifacts

Completed Agent Lab runs can be persisted locally as structured artifacts.

Artifacts may contain:

- session identifiers;
- target information;
- benchmark provenance;
- timestamps;
- observer provenance;
- execution results;
- technical reports;
- evaluation evidence.

Users should treat persistent run artifacts as measurement records.

If task inputs or outputs contain sensitive information, the resulting artifact may also be sensitive.

DLLO does not assume that all artifacts are safe for public distribution.

---

## 17. Observer identity

DLLO uses fields such as:

```text
observer_id
```

to support reproducibility and comparison semantics.

An observer identifier represents the provenance identity used by the measurement system.

It should not be interpreted as requiring a real-world legal identity.

Deployments should choose observer identifiers appropriate to their privacy requirements.

---

## 18. Region provenance

DLLO uses:

```text
region_code
```

to represent the region from which an observation was made.

This is measurement provenance.

It does not establish:

- exact physical location;
- home address;
- GPS coordinates;
- provider datacenter location;
- provider routing path.

For example:

```text
Observed from CL-Los-Lagos
```

does not imply:

```text
Served from a datacenter in Chile
```

---

## 19. Geographic precision

The current Observatory methodology needs sufficient regional provenance for reproducible geographic comparison.

It does not require precise personal geolocation.

Deployments should prefer the least precise location information that still satisfies the intended comparison semantics.

Exact residential addresses or GPS coordinates are not required by the core Observatory comparison model.

---

## 20. Time provenance

DLLO records timestamps such as:

```text
started_at_utc
finished_at_utc
completed_at_utc
```

where required by the workflow.

Time provenance is necessary for:

- temporal comparison;
- geographic skew checks;
- reproducibility;
- historical ordering.

These timestamps describe measurement events.

They should not be repurposed for unrelated user profiling.

---

## 21. Session identifiers

Agent Lab uses UUID-based session identifiers.

Exact session identifiers support reproducible history resolution.

DLLO intentionally avoids fuzzy identifiers such as:

```text
latest
recent session
UUID prefix
```

This reduces ambiguity when historical artifacts are selected.

Session identifiers are measurement references rather than user identity claims.

---

## 22. Agent Starter

Agent Starter processes information needed to determine feasible and appropriate agent architectures.

Possible inputs include:

- user goal;
- declared constraints;
- declared preferences;
- observed hardware information;
- capability information;
- technical compatibility evidence;
- candidate properties;
- catalog metadata.

Every decision-relevant input should retain explicit provenance.

---

## 23. Hardware information

Agent Starter can consume a `HardwareProfile`.

Current hardware schema can include information such as:

```text
device class
profile source
CPU model
logical CPU count
total memory
GPU information when available
```

Hardware information is used for technical feasibility and compatibility.

It should not be collected merely because it is available.

---

## 24. Hardware observation boundaries

Hardware visibility varies by platform.

Desktop, browser, mobile, and application environments may expose different information.

An unavailable hardware property should remain:

```text
UNKNOWN
```

rather than being guessed.

The system should distinguish between:

```text
not observed
```

and:

```text
not present
```

---

## 25. Source-code privacy

Coding-agent workflows can model requirements such as:

```text
source_code_must_stay_local
```

This is a hard privacy boundary when declared by the user.

A candidate that requires remote source-code processing conflicts with that requirement.

DLLO must not silently relax the constraint to produce a recommendation.

---

## 26. Knowledge-data privacy

Knowledge / RAG workflows can model:

```text
knowledge_data_must_stay_local
```

This requirement concerns where user knowledge data may be processed.

It is separate from:

```text
offline capability
```

A local-data requirement may permit some network dependency that does not transmit the protected knowledge data.

An offline requirement concerns connectivity rather than the privacy boundary itself.

---

## 27. Voice privacy

Voice workflows distinguish at least two potentially sensitive data classes:

```text
raw audio
transcript
```

DLLO can represent requirements such as:

```text
raw_audio_must_stay_local

transcript_must_stay_local
```

These constraints are independent.

An architecture may process raw audio locally while sending transcript text remotely, or vice versa.

The recommendation engine should evaluate the declared boundary rather than assume the two are equivalent.

---

## 28. Persistent memory

Personal-assistant workflows may involve persistent memory.

Relevant requirements can include:

- cross-session memory;
- selective memory;
- inspection of stored memory;
- editing stored memory;
- deletion of stored memory.

Persistent memory introduces a different privacy profile from session-only operation.

Agent Starter therefore treats memory architecture as an explicit candidate property rather than assuming all assistants should retain information indefinitely.

---

## 29. Selective memory

When selective memory is required, candidate support for:

```text
inspect
edit
delete
```

must be established explicitly.

An opaque memory system should not be represented as equivalent to a user-controlled memory system.

The ability to retain data is not the same as the ability to govern retained data.

---

## 30. Offline operation

Offline operation is modeled independently from privacy.

An offline requirement may mean that a capability must remain available without network connectivity.

For example:

```text
inference offline
knowledge retrieval offline
voice processing offline
```

Offline capability must be established through candidate evidence.

It must not be inferred merely because an architecture is described as local.

---

## 31. Local execution preference

Agent Starter may model a preference for local execution.

A preference is not equivalent to a privacy requirement.

```text
prefer_local_execution
```

is a soft preference when modeled as such.

It must not silently become:

```text
data must never leave device
```

unless the user explicitly declares that hard constraint.

---

## 32. Catalog privacy metadata

Agent Starter catalog information may include properties relevant to:

- execution location;
- remote processing;
- privacy implications;
- runtime requirements.

Catalog entries are technical metadata.

They should not contain user observation records or personal session data.

Catalog snapshots and user recommendation evidence are separate concerns.

---

## 33. Recommendation reports

Agent Starter final reports can contain:

- observed evidence;
- declared evidence;
- derived evidence;
- unknown evidence;
- requirements;
- requested capabilities;
- candidate explanations;
- recommendation results;
- concrete stack information.

A recommendation report may therefore reflect user-declared constraints.

Users should review reports before publishing them if those declarations contain information they consider sensitive.

---

## 34. Data minimization

The general DLLO rule is:

```text
collect what is necessary
retain what is justified
share only what is intended
```

Adding a field merely because it might become useful later is not sufficient justification.

New telemetry or provenance should have an explicit methodological purpose.

---

## 35. Purpose limitation

Information collected for measurement should not silently acquire unrelated purposes.

For example:

```text
region provenance
```

exists to support observation context and geographic comparison.

It should not become a mechanism for precise personal tracking.

Similarly:

```text
hardware profile
```

exists for feasibility and compatibility.

It should not become a general device fingerprinting system.

---

## 36. Sharing

DLLO currently centers on local workflows rather than a mandatory centralized upload service.

A locally persisted observation or artifact is not automatically public.

Before sharing artifacts externally, users should consider whether they contain:

- task inputs;
- task outputs;
- response text;
- user-declared constraints;
- source material;
- persistent-memory content;
- environment information.

Public distribution should be an explicit action.

---

## 37. Future distributed observations

DLLO is architected to support observations from independent observers.

A future distributed observation layer may require transmission or publication of qualified artifacts.

Any such public service should preserve:

- data minimization;
- explicit user intent;
- artifact provenance;
- privacy boundaries;
- versioning;
- integrity;
- clear publication semantics.

The current repository does not imply that all local artifacts are automatically uploaded to a global service.

---

## 38. Public Observatory boundary

The current repository provides:

- local observation workflows;
- local persistence;
- qualification;
- pair discovery;
- comparison;
- browser-to-observer bridges.

It does not currently represent an already-deployed global public data collection network.

Therefore:

```text
distributed-observation architecture
                !=
automatic cloud collection
```

---

## 39. Logs and errors

Diagnostic errors can themselves expose information.

When adding logging or error reporting, contributors should avoid unnecessarily including:

- secrets;
- authentication material;
- complete private prompts;
- private document contents;
- local filesystem contents;
- unrelated environment data.

Useful diagnostics should remain scoped to the failure being investigated.

---

## 40. Filesystem tasks

Some benchmark tasks intentionally operate on temporary or explicit filesystem workspaces.

Filesystem evidence should remain scoped to the benchmark workspace.

A filesystem benchmark is not permission to inspect unrelated user files.

Fixture materialization and evidence collection should operate within the explicit task boundary.

---

## 41. Credentials

DLLO should not require provider passwords, browser-session cookies, or exported authentication tokens for Consumer Probe measurements.

If future integrations require credentials through documented public APIs, those integrations should define:

- why the credential is needed;
- where it is stored;
- how long it is retained;
- which component can access it.

Secrets must not be embedded in observation artifacts unless explicitly required by a documented contract.

---

## 42. Privacy and reproducibility

Privacy and reproducibility can create tension.

More provenance can improve reproducibility, while excessive provenance can unnecessarily identify an observer or environment.

DLLO therefore favors:

> the minimum provenance sufficient to reproduce the measurement semantics.

For example, a regional code may support geographic comparison without requiring exact coordinates.

---

## 43. Legacy artifacts

Historical artifacts may contain fields produced under older schema versions.

Legacy artifacts remain inspectable when structurally valid.

New privacy assumptions should not be retroactively fabricated for old artifacts.

If an old artifact lacks a field required to establish a privacy property, that property should remain unknown.

---

## 44. User responsibility

DLLO provides technical mechanisms and privacy-oriented boundaries.

Users remain responsible for deciding whether they have the right to process, retain, benchmark, or share the data they provide to a workflow.

In particular, users should avoid supplying confidential or regulated information unless they understand the resulting local artifact and execution path.

---

## 45. Contributor requirements

New DLLO features that collect or persist information should document:

```text
what is collected
why it is collected
where it is stored
whether it can leave the device
how it affects reproducibility
whether it contains user content
```

A feature should not introduce new collection silently.

---

## 46. Privacy review checklist

Before adding a new data field or collection mechanism, ask:

```text
Is this field required for the workflow?

Is it OBSERVED, DECLARED, DERIVED, or UNKNOWN?

Could a less sensitive field provide the same methodological value?

Is it stored locally?

Can it leave the local machine?

Is sharing explicit?

Could it contain user content?

Could it expose credentials or session state?

Does it reveal more geographic precision than required?

Could it become a device fingerprint?

Does the user understand why it is collected?

Can the workflow operate without it?

What happens when the value is unavailable?
```

If the purpose cannot be clearly stated, the field should not be collected.

---

## 47. Privacy non-goals

DLLO is not intended to become:

- a user-tracking platform;
- a precise geolocation system;
- a browser-session extraction tool;
- a cookie collection system;
- a provider credential harvester;
- a private-interface scraper;
- a device fingerprinting service;
- an automatic cloud uploader for local observations.

Its privacy model exists to support reproducible measurement with the smallest justified data surface.

---

## 48. Summary

The DLLO privacy model can be summarized as:

```text
MINIMIZE
Collect only what is justified.
        |
        v
SEPARATE
Keep privacy, locality, and connectivity distinct.
        |
        v
PRESERVE
Retain provenance needed for reproducibility.
        |
        v
CONTROL
Keep local capture separate from sharing.
        |
        v
DISCLOSE
Make collection and limitations explicit.
```

---

## Core principle

> **Collect only what the measurement requires, preserve only what the evidence justifies, and share only what the user intends.**
