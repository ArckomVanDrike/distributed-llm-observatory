# DLLO Observer Protocol

## Agent Protocol Core 1.0

Status: stable.

Agent Protocol Core 1.0 is the stable behavioral freeze of
`agent-protocol-core` version `0.10`.

Version 1.0 introduces no new benchmark capability. It preserves the
qualified task set and promotes the existing protocol contract to a
stable version.

### Scope

Agent Protocol Core 1.0 covers:

- exact output evaluation;
- instruction following;
- structured output;
- observed tool actions;
- semantic tool selection;
- ordered action sequences;
- runtime data propagation between tool calls;
- failure handling and recovery;
- conditional runtime branching;
- multi-branch runtime decisions.

### Observer and SUT boundary

The system under test receives only the public execution contract
required to perform the task.

SUT-visible action metadata is limited to:

- available tool names;
- tool descriptions;
- public tool parameter contracts;
- runtime gateway endpoints;
- temporary runtime authorization.

Observer-owned information is not exposed to the SUT before execution.
This includes expected actions, expected propagation, recovery
expectations, branch expectations, configured tool results or failures,
criterion evidence, and evaluation verdicts.

Runtime tool results and failures become visible to the SUT only through
actual interaction with the action gateway.

### Evaluation invariants

A benchmark task may use at most one advanced action evaluation mode.

Runtime branch matching uses JSON scalar semantics consistently between
schema validation and observer evidence collection. Numerically
equivalent JSON numbers compare equal, while booleans remain distinct
from numbers.

Evaluation evidence is collected independently by the observer and does
not rely on SUT self-certification.

### Versioning

Published Agent Protocol Core suite versions remain exactly resolvable.

Version 1.0 preserves the same canonical task sequence and
`sut_protocol` harness profile as version 0.10. Version 0.10 remains
available as an inactive historical suite, while version 1.0 is the
single active Agent Protocol Core suite.

Published suite history is monotonic: later protocol versions extend or
freeze the established task sequence without rewriting historical suite
definitions.

### Qualification

The executable qualification contract is maintained in:

`tests/unit/test_agent_protocol_v1_readiness.py`

The v1 qualification also relies on canonical asset tests, local HTTP
SUT end-to-end tests, deterministic observer-owned evidence tests, and
the full repository quality gate.

### Out of scope for 1.0

The following capabilities are not required by Agent Protocol Core 1.0:

- loops;
- parallel tool execution;
- nested or arbitrary planning graphs;
- persistent long-term memory;
- human approval workflows.

These capabilities may be introduced in later protocol versions without
changing the Agent Protocol Core 1.0 contract.
