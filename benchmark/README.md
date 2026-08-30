# DLLO Benchmark Bank

The `benchmark/` directory contains the versioned benchmark assets used by Distributed LLM Observatory (**DLLO**).

These assets define prompts, executable tasks, fixtures, and benchmark suites independently from the runtime code that loads and evaluates them.

The central rule is:

> **Published benchmark behavior must remain explicitly versioned and reproducible.**

---

## 1. Current structure

The current benchmark tree is organized as:

```text
benchmark/
|
|-- prompts/
|   |-- coding/
|   |-- instruction_following/
|   |-- knowledge/
|   |-- mathematics/
|   |-- reasoning/
|   |-- technical/
|   `-- writing/
|
|-- tasks/
|   `-- agent/
|       |-- filesystem/
|       `-- protocol/
|
|-- fixtures/
|   `-- agent/
|       `-- filesystem/
|
|-- suites/
|   `-- agent/
|
`-- README.md
```

The directories serve different purposes.

```text
prompt
    !=
task
    !=
fixture
    !=
suite
    !=
evaluator
```

---

## 2. Prompt bank

Generic prompt-based benchmarks live under:

```text
benchmark/prompts/
```

Current prompt categories include:

```text
coding
instruction_following
knowledge
mathematics
reasoning
technical
writing
```

Prompt files are loaded through:

```text
observer/core/prompt_bank.py
```

`PromptBank`:

- recursively loads JSON prompt files;
- validates them against the benchmark prompt schema;
- rejects invalid JSON;
- rejects invalid schema content;
- rejects duplicate `prompt_id` values;
- can expose only enabled prompts.

The default CLI prompt-bank path is:

```text
benchmark/prompts
```

---

## 3. Task bank

Executable structured benchmark tasks live under:

```text
benchmark/tasks/
```

Current Agent Lab tasks include filesystem and Agent Protocol tasks.

Task files are loaded through:

```text
observer/core/task_bank.py
```

`TaskBank`:

- recursively discovers JSON task files;
- validates each file against `BenchmarkTask`;
- rejects invalid JSON;
- rejects invalid task schemas;
- rejects duplicate `task_id` values;
- can return only enabled tasks.

The default task-bank path used by the CLI and Agent Lab is:

```text
benchmark/tasks
```

---

## 4. Current Agent Protocol tasks

The current Agent Protocol task bank includes tasks covering:

```text
smoke execution
instruction following
structured output
observed actions
tool selection
ordered action sequences
runtime data propagation
failure recovery
conditional branching
multi-branch decisions
```

Current files include:

```text
agent-protocol-smoke-001.json
agent-protocol-instruction-001.json
agent-protocol-structured-output-001.json
agent-protocol-action-001.json
agent-protocol-tool-selection-001.json
agent-protocol-action-sequence-001.json
agent-protocol-data-flow-001.json
agent-protocol-recovery-001.json
agent-protocol-branch-001.json
agent-protocol-multi-branch-001.json
agent-protocol-multi-branch-002.json
```

These tasks form the behavioral building blocks assembled into versioned protocol suites.

---

## 5. Filesystem task

The repository also contains the filesystem benchmark task:

```text
benchmark/tasks/agent/filesystem/agent-filesystem-001.json
```

Filesystem tasks use explicit benchmark fixtures rather than arbitrary user files.

This keeps execution inside a defined benchmark workspace.

---

## 6. Fixture bank

Benchmark fixtures live under:

```text
benchmark/fixtures/
```

Current filesystem fixture assets include:

```text
benchmark/fixtures/agent/filesystem/filesystem-empty-v0-1.json
```

Fixtures are loaded through:

```text
observer/core/fixture_bank.py
```

`FixtureBank`:

- recursively loads JSON fixture files;
- validates them against `FilesystemFixture`;
- rejects invalid JSON;
- rejects invalid fixture schemas;
- rejects duplicate `fixture_id` values.

Fixtures provide controlled task environments.

They are not permission to inspect arbitrary user filesystem content.

---

## 7. Suites

Benchmark suites live under:

```text
benchmark/suites/
```

A suite defines a versioned collection and ordering of benchmark tasks.

Current Agent suite assets include:

```text
agent-core-v0-1.json

agent-protocol-core-v0-1.json
agent-protocol-core-v0-2.json
agent-protocol-core-v0-3.json
agent-protocol-core-v0-4.json
agent-protocol-core-v0-5.json
agent-protocol-core-v0-6.json
agent-protocol-core-v0-7.json
agent-protocol-core-v0-8.json
agent-protocol-core-v0-9.json
agent-protocol-core-v0-10.json
agent-protocol-core-v1-0.json
```

Suite files are loaded through:

```text
observer/core/suite_bank.py
```

---

## 8. Suite identity

A benchmark suite is identified by:

```text
suite_id
suite_version
```

The pair forms the suite identity.

`SuiteBank` rejects duplicate identities.

Conceptually:

```text
("agent-protocol-core", "1.0")
```

is distinct from:

```text
("agent-protocol-core", "0.10")
```

even when the later release intentionally freezes the same qualified behavior.

---

## 9. Exact suite resolution

Suites are resolved through:

```text
observer/core/suite_registry.py
```

Resolution is explicit:

```text
suite_id
    +
suite_version
    |
    v
exact suite
    |
    v
ordered task IDs
    |
    v
resolved BenchmarkTask objects
```

There is no implicit:

```text
latest
```

suite lookup inside exact historical resolution.

---

## 10. Historical versions

Published suite versions remain available so historical observations can retain their original benchmark semantics.

DLLO favors:

```text
new behavior
    ->
new version
```

instead of:

```text
modify old published suite in place
```

This is essential for reproducibility.

---

## 11. Agent Protocol Core 1.0

**Agent Protocol Core 1.0 is stable.**

The corresponding suite asset is:

```text
benchmark/suites/agent/agent-protocol-core-v1-0.json
```

Version 1.0 is the stable behavioral freeze of the qualified `0.10` protocol sequence.

It does not introduce a new capability merely because the major version changed.

Instead, it promotes the qualified contract to stable status.

See:

[`../docs/observer-protocol.md`](../docs/observer-protocol.md)

---

## 12. Protocol version progression

The Agent Protocol Core suite history documents the incremental construction of the behavioral protocol.

Published historical assets remain present:

```text
0.1
0.2
0.3
0.4
0.5
0.6
0.7
0.8
0.9
0.10
1.0
```

Later versions do not erase the existence of earlier ones.

This allows a historical observation to remain tied to its original suite.

---

## 13. Suite task ordering

A suite contains an ordered set of task IDs.

`SuiteRegistry` resolves those IDs in suite order.

The ordering is part of the suite contract.

It should therefore not be treated as an arbitrary filesystem ordering.

Conceptually:

```text
suite.task_ids
      |
      v
task 1
task 2
task 3
...
```

Changing task order may change protocol behavior and should be treated as a versioned contract change when semantically relevant.

---

## 14. Missing task protection

Suite resolution fails if a referenced task does not exist.

A suite must not silently skip missing task assets.

Conceptually:

```text
suite
  |
  +-- task A  -> exists
  |
  +-- task B  -> missing
                  |
                  v
                ERROR
```

This prevents partial execution from masquerading as the complete published suite.

---

## 15. Family compatibility

A task referenced by a suite must belong to the same benchmark family as the suite.

A family mismatch causes suite resolution to fail.

This prevents accidental composition of semantically unrelated task types.

---

## 16. Target compatibility

DLLO targets declare a type and capabilities.

Examples include:

```text
FOUNDATION_MODEL
AGENT
AI_SYSTEM
```

and capabilities such as:

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

Benchmark compatibility is checked before incompatible workloads are executed.

A benchmark should not silently assume capabilities the target does not declare.

---

## 17. Harness profile

Suites may also be associated with an explicit benchmark harness profile.

`SuiteRegistry` can filter enabled suite candidates using:

```text
target type
+
harness profile
```

This makes runtime expectations part of suite resolution rather than an implicit external assumption.

---

## 18. Unique enabled suite resolution

When resolving an enabled suite for a target and harness profile, DLLO requires a unique match.

Conceptually:

```text
0 matching enabled suites
    ->
error

1 matching enabled suite
    ->
resolve it

>1 matching enabled suites
    ->
ambiguity error
```

DLLO does not silently select the first candidate.

---

## 19. Enabled vs historical

Bank loaders distinguish between:

```text
all assets
```

and:

```text
enabled assets
```

Historical assets can remain available for exact resolution even when they are no longer the currently enabled protocol.

This supports both:

```text
current execution
```

and:

```text
historical reproducibility
```

without deleting old contracts.

---

## 20. Evaluators

Benchmark tasks are evaluated through observer-owned evaluator implementations.

Evaluator code lives primarily under:

```text
observer/core/
```

Current evaluator families include:

```text
deterministic task evaluation
exact output
JSON structure
observed action evidence
filesystem evidence
```

The task describes the evaluation contract.

The evaluator applies that contract to observer-owned evidence.

---

## 21. Evidence before verdict

The benchmark methodology follows:

```text
SUT execution
      |
      v
Observer evidence
      |
      v
Evaluator
      |
      v
Criterion results
      |
      v
Task result
```

The system under test does not decide its own PASS / FAIL state.

---

## 22. Observer-owned expectations

Verifier-only expectations remain outside the public SUT execution contract.

They can include:

- expected outputs;
- expected tool selection;
- expected action order;
- expected runtime propagation;
- recovery expectations;
- branch expectations;
- configured tool results;
- configured failures;
- criterion evidence.

The SUT receives only information required to execute the task.

---

## 23. Runtime data

When a task requires runtime information to become visible to the agent, it is delivered through the actual runtime interaction.

For example:

```text
agent calls tool
      |
      v
action gateway
      |
      v
runtime tool result
      |
      v
agent receives result
      |
      v
next action
```

The expected result is not simply leaked to the agent in advance.

---

## 24. Advanced action modes

Agent Protocol Core can evaluate advanced behaviors including:

- action sequences;
- runtime propagation;
- recovery;
- branching;
- multi-branch decisions.

A task may use at most one advanced action evaluation mode.

This keeps evaluator semantics unambiguous.

---

## 25. Task discovery CLI

DLLO exposes task discovery commands.

List enabled tasks:

```bash
dllo task-list
```

Show one task:

```bash
dllo task-show <task-id>
```

By default these commands use:

```text
benchmark/tasks
```

An alternate task-bank path can be supplied explicitly.

---

## 26. Prompt execution

Generic prompt-based benchmark execution uses the prompt bank.

The default path is:

```text
benchmark/prompts
```

Prompt loading is separate from Agent Protocol suite resolution.

This distinction is intentional.

```text
prompt benchmark
      !=
Agent Protocol task suite
```

---

## 27. Agent Lab suite execution

Agent Lab uses:

```text
benchmark/suites
benchmark/tasks
```

as the default suite and task roots.

The protocol runner resolves the suite through the same bank and registry contracts documented above.

---

## 28. JSON assets

Current benchmark assets are JSON.

Loading always includes:

```text
read JSON
    |
    v
schema validation
    |
    v
typed benchmark object
```

Invalid JSON or invalid schema content causes an explicit error.

Malformed files are not silently ignored.

---

## 29. Duplicate identity protection

The banks enforce uniqueness at their relevant identity level.

Current rules include:

```text
PromptBank
    -> unique prompt_id

TaskBank
    -> unique task_id

FixtureBank
    -> unique fixture_id

SuiteBank
    -> unique (suite_id, suite_version)
```

Duplicate identities produce errors.

---

## 30. Deterministic discovery

Files are discovered using sorted recursive traversal.

This keeps asset loading deterministic.

However, suite task execution order comes from the explicit suite task list rather than filesystem order.

---

## 31. Adding a prompt

When adding a prompt:

1. create a JSON asset under the appropriate `benchmark/prompts/` category;
2. use a unique `prompt_id`;
3. validate against the current prompt schema;
4. add or update tests where behavior changes;
5. avoid silently changing an already published prompt when historical reproducibility matters.

---

## 32. Adding a task

When adding a structured benchmark task:

1. create the JSON task under the appropriate `benchmark/tasks/` family;
2. assign a unique `task_id`;
3. declare required capabilities explicitly;
4. define evaluator semantics explicitly;
5. preserve observer-owned expectations;
6. add task-level tests;
7. update or create a suite version when the task becomes part of a published protocol.

A new task should not be inserted into an existing historical suite merely for convenience.

---

## 33. Adding a fixture

When a benchmark requires controlled environment state:

1. create a fixture under `benchmark/fixtures/`;
2. assign a unique `fixture_id`;
3. validate against the fixture schema;
4. keep fixture behavior scoped to the benchmark workspace;
5. add tests for materialization and evidence collection where relevant.

Fixtures should be deterministic whenever the benchmark requires reproducibility.

---

## 34. Adding a suite

When creating a suite:

1. define an explicit `suite_id`;
2. define an explicit `suite_version`;
3. declare its benchmark family;
4. declare its harness profile where applicable;
5. list task IDs explicitly and in canonical order;
6. ensure every referenced task exists;
7. ensure every referenced task belongs to the same family;
8. add qualification and regression tests.

If the suite changes semantically, prefer a new version.

---

## 35. Changing a published suite

Published historical suites should be treated as immutable contracts unless correcting a demonstrable repository defect under a documented migration policy.

Normally:

```text
semantic change
    ->
new suite version
```

not:

```text
semantic change
    ->
rewrite previous version
```

Historical observations depend on this stability.

---

## 36. Qualification

A stable benchmark protocol should be supported by executable tests.

Agent Protocol Core 1.0 qualification includes dedicated readiness and asset verification together with end-to-end protocol tests.

The repository test suite is part of the release gate.

Documentation alone does not qualify a protocol.

---

## 37. Benchmark reproducibility

A reproducible benchmark observation should preserve enough information to identify:

```text
target
suite ID
suite version
task coverage
observer provenance
execution timing
evidence
evaluation
```

The suite version is especially important.

A benchmark family name alone is not sufficient historical provenance.

---

## 38. Benchmark assets and Observatory comparison

Observatory comparison requires compatible benchmark semantics.

Two observations should not be compared merely because they involve the same target.

Relevant comparability includes:

```text
suite identity
suite version
task coverage
```

Mixing incompatible benchmark contracts can create meaningless differences.

---

## 39. No hidden latest

The benchmark bank follows the same explicit-selection rule as the rest of DLLO.

Do not introduce APIs that silently mean:

```text
give me whatever the latest suite is
```

when historical reproducibility requires an exact contract.

Current execution may resolve a unique enabled suite under explicit conditions.

Historical resolution remains version-specific.

These are different operations.

---

## 40. No global benchmark score

Benchmark tasks and suites should not automatically collapse heterogeneous behavior into one universal model or agent score.

DLLO preserves task evidence and criterion results.

A future aggregation methodology would need to be explicit, versioned, and justified.

---

## 41. Benchmark review checklist

Before publishing or modifying a benchmark asset, ask:

```text
Does the asset have a unique identity?

Is its schema valid?

Is the target family explicit?

Are required capabilities explicit?

Is evaluator behavior explicit?

Are verifier-only expectations hidden from the SUT?

Does runtime information reach the SUT only through legitimate execution?

Is task ordering explicit?

Does the suite reference every required task?

Would this change alter an existing published contract?

If yes, should this become a new version?

Can an old observation still resolve its original suite exactly?

Are relevant tests present?
```

---

## 42. Current stable protocol

The current stable Agent Protocol contract is:

```text
Agent Protocol Core 1.0
```

with suite asset:

```text
benchmark/suites/agent/agent-protocol-core-v1-0.json
```

See:

- [`../docs/observer-protocol.md`](../docs/observer-protocol.md)
- [`../docs/methodology.md`](../docs/methodology.md)
- [`../docs/architecture.md`](../docs/architecture.md)

---

## Core principle

> **Version benchmark semantics explicitly, preserve historical contracts, and evaluate observable evidence rather than SUT claims.**
