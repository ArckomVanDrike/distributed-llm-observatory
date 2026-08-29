# DLLO Methodology

Distributed LLM Observatory (**DLLO**) is designed to produce observations, evaluations, recommendations, and comparisons that remain traceable to explicit evidence.

The central methodological rule is:

> **Observe first. Compare carefully. Explain only when the evidence allows it.**

DLLO deliberately separates:

```text
measurement
evaluation
recommendation
comparison
explanation
```

because these operations answer different questions and require different evidence.

---

## 1. Scope

DLLO currently applies this methodology across three principal workflows:

```text
Agent Starter
    |
    v
What architecture and stack can reasonably satisfy the user's needs?

Test Your Agent
    |
    v
What did the agent actually do under a defined protocol?

Observatory
    |
    v
What changed between compatible observations?
```

The same evidence discipline applies across all three.

---

## 2. Epistemic rule

DLLO distinguishes between:

```text
what was observed
what was declared
what was derived
what remains unknown
what can be evaluated
what can be compared
what can reasonably be concluded
```

A system should not make a stronger claim than its evidence supports.

For example:

```text
Observed:
latency increased

Supported conclusion:
latency was higher in this observation

Unsupported automatic conclusion:
the provider was saturated
```

The latter may become a hypothesis.

It is not an observation unless independent evidence establishes it.

---

## 3. Observation is not explanation

A measurement describes an observable result.

It does not automatically establish its underlying cause.

DLLO therefore treats the following as different layers:

```text
Observation
    |
    v
Comparison
    |
    v
Observed difference
    |
    v
Possible hypothesis
    |
    v
Independent causal evidence
```

Only the first three are directly produced by the Observatory comparison workflow.

Causal interpretation requires evidence outside the comparison itself.

---

## 4. Evidence provenance

Decision-relevant information should preserve where it came from.

Agent Starter formalizes four provenance classes:

```text
OBSERVED
DECLARED
DERIVED
UNKNOWN
```

### OBSERVED

Information directly obtained from an observable environment or measurement.

Examples may include:

- hardware characteristics;
- operating-system information;
- benchmark outcomes;
- recorded action sequences;
- timings;
- task evidence.

Observed information should describe what the observer could actually establish.

---

### DECLARED

Information explicitly provided by the user or operator.

Examples include:

- source code must remain local;
- offline operation is required;
- citations are required;
- persistent memory is required;
- a workflow is deterministic.

Declared information represents user intent or constraints.

It must not be silently replaced by inferred preferences.

---

### DERIVED

Information deterministically produced from existing evidence.

Examples include:

```text
declared requirement
        |
        v
derived required capability
```

or:

```text
observed / declared inputs
        |
        v
technical requirement
```

Derived evidence should remain traceable to the evidence that produced it.

---

### UNKNOWN

The available evidence is insufficient to establish the property.

UNKNOWN is a first-class state.

```text
UNKNOWN != FALSE

UNKNOWN != NOT_FEASIBLE

UNKNOWN != UNSUPPORTED
```

Unknown information should normally reduce confidence or prevent a stronger conclusion.

It should not be converted into positive or negative evidence merely to simplify a decision.

---

## 5. System Under Test / Observer separation

DLLO separates the **System Under Test (SUT)** from the observer.

The SUT performs the task.

The observer defines and collects the evidence required to evaluate it.

```text
Task
  |
  v
SUT execution
  |
  v
Observer-owned evidence
  |
  v
Evaluation
```

The SUT does not receive verifier-only information before execution.

Observer-owned information may include:

- expected actions;
- expected action ordering;
- expected runtime propagation;
- recovery expectations;
- branch expectations;
- configured tool results;
- configured tool failures;
- criterion evidence;
- evaluation verdicts.

The SUT receives only the public execution contract needed to perform the task.

---

## 6. No SUT self-certification

A system under test cannot establish success merely by reporting that it succeeded.

For example:

```text
SUT:
"Task completed successfully."
```

is not sufficient evidence of task success.

Instead:

```text
Observed output
Observed actions
Observed tool interactions
Observed runtime propagation
Observed recovery behavior
        |
        v
Observer evaluation
```

determine the result.

This protects the distinction between:

```text
claim
```

and:

```text
evidence
```

---

## 7. Benchmark execution

A benchmark observation should preserve enough information to identify:

- target;
- benchmark suite;
- suite version;
- task;
- execution conditions;
- observer context;
- result;
- collected evidence.

Published benchmark and protocol versions should remain exactly resolvable.

Historical suite definitions should not be silently rewritten after publication.

This allows an old observation to remain interpretable even after newer suites are introduced.

---

## 8. Protocol versioning

Agent Protocol Core 1.0 is the stable behavioral freeze of the qualified `agent-protocol-core` 0.10 sequence.

Versioning follows the principle:

```text
new contract
    |
    v
new explicit version

not

rewrite old historical contract
```

A published observation should remain associated with the protocol semantics that produced it.

---

## 9. Observer-owned task evidence

DLLO evaluates benchmark behavior through evidence collected independently of SUT self-reporting.

Depending on the task, evidence may include:

- exact outputs;
- structured outputs;
- observed tool actions;
- tool selection;
- action order;
- runtime values passed between actions;
- failures;
- retries;
- recovery actions;
- branch decisions.

Evidence collection and evaluation remain separate concerns.

```text
collect evidence
       |
       v
apply evaluator
```

The evaluator should operate on the evidence rather than reconstructing behavior from unsupported assumptions.

---

## 10. Advanced action evaluation

Agent Protocol Core supports several forms of agent behavior evaluation, including:

- observed tool actions;
- semantic tool selection;
- ordered action sequences;
- runtime data propagation;
- recovery;
- conditional branching;
- multi-branch decisions.

A benchmark task may use at most one advanced action evaluation mode.

This keeps task semantics explicit and prevents multiple overlapping advanced evaluation contracts from making the verdict ambiguous.

---

## 11. Runtime semantics

Runtime information becomes visible to the SUT through actual interaction with the execution environment.

For example:

```text
tool call
   |
   v
runtime result
   |
   v
SUT receives result
   |
   v
next action
```

Observer-configured expectations are not exposed in advance.

For branch matching, DLLO uses JSON scalar semantics consistently.

Numerically equivalent JSON numbers compare equal.

Booleans remain distinct from numbers.

---

## 12. Evaluation

Evaluation answers:

> Did the observed evidence satisfy the task's explicit criteria?

It should not answer:

> Did the SUT say that it satisfied the task?

Evaluation should be:

- based on explicit criteria;
- reproducible;
- version-aware;
- traceable to observed evidence.

---

## 13. Quality evaluation

DLLO also defines a multidimensional response-quality schema.

Current dimensions are:

```text
fit
efficiency
clarity
style
structure
technical_accuracy
overall
```

Each dimension uses an integer scale from:

```text
1 .. 6
```

The individual dimensions are not collapsed into an unconstrained arithmetic average.

The schema enforces consistency between dimensional failures and the overall score.

Current invariants include:

```text
if any dimension == 1:
    overall <= 2

if any dimension == 2:
    overall <= 3

if every dimension >= 4:
    overall >= 4
```

This prevents a severe weakness in one quality dimension from being hidden by strong scores elsewhere.

Detailed scoring interpretation belongs in:

[`quality-rubric.md`](quality-rubric.md)

---

## 14. Run artifacts

A completed Agent Lab execution may be stored as a persistent run artifact.

The artifact is intended to preserve enough evidence and provenance for later inspection.

Conceptually:

```text
Execution
    |
    v
Evidence
    |
    v
Evaluation
    |
    v
Technical report
    |
    v
Persistent run artifact
```

Persistence does not automatically imply Observatory qualification.

---

## 15. Valid artifact vs qualified observation

DLLO distinguishes:

```text
valid run artifact
```

from:

```text
Observatory-qualified observation
```

A historical artifact may remain structurally valid and useful even if it lacks sufficient provenance for a newer comparison workflow.

Qualification is derived from artifact contents.

It is not a self-declared property.

---

## 16. Observation provenance

Observatory comparison depends on explicit provenance.

Depending on the workflow, relevant provenance includes:

- observer identity;
- observation region;
- observation time;
- target identity;
- suite identity;
- suite version;
- task coverage.

Missing provenance should remain visible as missing.

It should not be silently fabricated.

---

## 17. Observation region

DLLO treats region as **observation provenance**.

For example:

```text
Observed from CL-Los-Lagos
```

means that the observation originated from that observer context.

It does not mean:

```text
Served from a datacenter in Chile
```

The observer does not infer provider serving location from client region.

Therefore:

```text
observer region != serving location
```

unless independent evidence explicitly establishes such a relationship.

---

## 18. Comparability before comparison

Two observations should only be compared when their semantics are sufficiently compatible.

The general rule is:

```text
observation A
      +
observation B
      |
      v
comparability assessment
      |
      +------ incompatible ------> visible rejection reason
      |
      v
comparison
```

Comparison must not silently mix incompatible:

- targets;
- benchmark suites;
- suite versions;
- task coverage;
- required provenance.

---

## 19. Rejected pairs remain evidence

An incompatible pair is still useful information.

DLLO pair discovery therefore keeps rejected candidate pairs visible together with the reason they failed comparability.

It does not simply discard them.

This preserves the distinction between:

```text
no pair was considered
```

and:

```text
pair was considered but rejected for an explicit reason
```

---

## 20. Temporal comparison

Temporal comparison asks:

> What changed when a compatible target was observed again later from the same observation context?

Typical temporal compatibility requirements include:

- same target;
- same benchmark suite;
- same suite version;
- compatible task coverage;
- complete required provenance;
- same observer identity;
- same observation region;
- candidate after baseline.

The baseline and candidate remain explicit.

DLLO does not automatically choose the newest observation as the candidate.

---

## 21. Geographic comparison

Geographic comparison asks:

> What differences were observed from different regions under compatible benchmark conditions?

Typical requirements include:

- same target;
- same benchmark suite;
- same suite version;
- compatible task coverage;
- complete required provenance;
- different observation regions;
- observations sufficiently close in time.

The acceptable observation-time skew must be supplied explicitly.

There is no hidden global geographic skew threshold.

---

## 22. No hidden selection

DLLO avoids implicit selectors that can make results difficult to reproduce.

The Observatory should not silently choose:

```text
latest
best
baseline
candidate
comparison pair
geographic skew threshold
```

Selection should remain explicit in the input or resulting provenance.

---

## 23. Comparison output

An Observatory comparison is intended to describe observed change.

Examples include:

```text
task outcome changed

latency changed

failure behavior changed

tool-use behavior changed

recovery behavior changed
```

The comparison should preserve enough provenance to determine which two observations produced the result.

---

## 24. Agent Starter methodology

Agent Starter applies the same evidence discipline to recommendation rather than benchmark evaluation.

Its mission is:

> Given the user's goal, constraints, and available evidence, what architecture and stack can reasonably satisfy those requirements, and why?

Agent Starter separates:

```text
technical feasibility
```

from:

```text
recommendation
```

A system may be technically feasible without being a sensible recommendation.

---

## 25. Agent Starter decision order

Agent Starter uses the following conceptual order:

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

The order is intentional.

A product or model should not be selected first and rationalized afterward.

---

## 26. Technical feasibility

Technical feasibility asks:

> Can this candidate reasonably operate under the known technical conditions?

Current feasibility concepts include:

```text
FEASIBLE
LIMITED
NOT_FEASIBLE
UNKNOWN
```

Feasibility is determined from technical evidence.

It is not equivalent to recommendation.

---

## 27. Recommendation

Recommendation asks:

> Given the user's actual goal and constraints, should this candidate be used?

Current recommendation states include:

```text
RECOMMENDED
POSSIBLE
POSSIBLE_BUT_NOT_RECOMMENDED
NOT_RECOMMENDED
```

A candidate can therefore be technically possible while still being operationally inappropriate.

---

## 28. No global Agent Starter score

Agent Starter does not reduce candidate evaluation to one hidden scalar ranking.

Relevant evidence can remain multidimensional.

Examples include:

```text
technical fit
privacy fit
operational fit
constraint compatibility
capability coverage
evidence completeness
```

Multiple candidates may remain `RECOMMENDED`.

No hidden tie-break is introduced when the evidence does not justify one.

---

## 29. Hard constraints

A hard constraint represents a requirement that must not be silently violated.

Examples may include:

- source code must remain local;
- knowledge data must remain local;
- audio must remain local;
- transcript must remain local;
- offline operation is required.

If a candidate conflicts with a hard constraint, Agent Starter must not quietly weaken the requirement to produce a recommendation.

---

## 30. Soft preferences

A soft preference can influence recommendation status without becoming a hard blocker.

The methodological rule is:

```text
soft preference != hard constraint
```

and:

```text
soft preference cannot override hard failure
```

A preference should only influence decisions when its semantics are explicit and testable.

---

## 31. Privacy and connectivity

Agent Starter treats privacy and connectivity as separate dimensions.

```text
private != offline

local execution != offline capability
```

A local architecture may still depend on network services.

An offline architecture may not automatically satisfy every privacy requirement.

These properties should be represented independently.

---

## 32. Candidate properties require evidence

Agent Starter should not infer technical properties merely from an architecture identifier or human-readable name.

For example:

```text
architecture ID contains "local"
```

is not by itself sufficient proof of:

```text
offline capable
```

Decision-relevant candidate properties should be explicit evidence.

---

## 33. Catalog methodology

Concrete stack resolution uses explicit catalog snapshots.

The catalog is a source of component metadata.

It is not the reasoning engine.

The conceptual flow is:

```text
architecture requirements
        |
        v
catalog query
        |
        v
explicit snapshot
        |
        v
matching entries
        |
        v
concrete stack
```

There is no hidden `latest` catalog.

---

## 34. Catalog ambiguity

Catalog matching should preserve ambiguity rather than hiding it.

Conceptually:

```text
0 matches
    -> no selected component

1 match
    -> deterministic selection can be made

>1 matches
    -> preserve alternatives unless an explicit selection rule exists
```

The first item in a catalog must not become the winner merely because it appears first.

---

## 35. Recommendation explanations

Why / Why Not explanations should derive from the same evidence used by the decision engine.

They should not constitute a second independent reasoning system.

Conceptually:

```text
decision evidence
      |
      +------> recommendation
      |
      +------> Why / Why Not
```

This keeps explanation and verdict aligned.

---

## 36. Recommendation confidence

Confidence represents evidence completeness.

A recommendation with missing critical evidence should not be presented with unjustified certainty.

Current confidence concepts include:

```text
HIGH
MEDIUM
LIMITED
```

UNKNOWN evidence may reduce confidence even when it does not establish a negative result.

---

## 37. Adaptive questioning

Agent Starter should ask only questions that can affect:

- recommendation;
- required capability;
- technical feasibility;
- confidence.

A question that cannot change any of those outcomes should not be asked merely to collect more data.

This keeps the questionnaire decision-relevant rather than exhaustive for its own sake.

---

## 38. AI necessity

Agent Starter may conclude that a traditional deterministic solution is more appropriate than an AI agent.

The methodology does not assume:

```text
user asks about automation
        ->
must recommend an LLM agent
```

Architecture choice should follow the workload.

It should not begin from the assumption that AI is always required.

---

## 39. Reproducibility

A DLLO result should preserve enough context to reconstruct the reasoning or comparison that produced it.

For an observation, this means provenance such as:

```text
target
suite
suite version
task coverage
observer context
observation time
region provenance
```

For Agent Starter, this means:

```text
user goal
declared requirements
observed evidence
derived evidence
unknown factors
candidate evidence
catalog snapshot
decision result
```

Reproducibility is preferred over implicit convenience.

---

## 40. Historical stability

Historical artifacts should remain inspectable.

Historical protocol versions should remain resolvable.

Legacy observations should not disappear merely because later qualification rules become stricter.

The system should distinguish:

```text
historical validity
```

from:

```text
eligibility for a newer comparison
```

---

## 41. Privacy methodology

DLLO aims to collect only information required for:

- execution;
- evaluation;
- reproducibility;
- explicit comparison.

Consumer-facing measurement workflows are intentionally constrained.

DLLO does not treat access to a consumer interface as permission to collect unrelated private session information.

Detailed privacy rules are documented separately in:

[`privacy.md`](privacy.md)

---

## 42. Consumer Probe methodological boundary

Consumer Probe follows a human-in-the-loop model.

It is not intended to become a mechanism for:

- automatic prompt submission;
- private-interface scraping;
- browser session-token collection;
- cookie collection;
- private provider endpoint use;
- rate-limit bypass.

Consumer Probe should record what can legitimately be observed from the client context without claiming visibility into undocumented provider infrastructure.

---

## 43. Measurement uncertainty

Not every relevant property is observable.

When a property cannot be established, DLLO should preserve that limitation explicitly.

Examples:

```text
serving datacenter: UNKNOWN

provider routing decision: UNKNOWN

reason for increased latency: UNKNOWN
```

An unknown mechanism does not invalidate the observation itself.

It limits what can be concluded from it.

---

## 44. Hypotheses

DLLO observations can support hypothesis generation.

For example:

```text
Repeated observation:
higher failure rate in one period

Possible hypothesis:
provider-side change

Methodological status:
not established by observation alone
```

Independent evidence would be required to elevate the hypothesis into a factual causal claim.

---

## 45. Scientific scope

DLLO can support investigation of patterns such as:

- temporal behavioral variation;
- regional differences in observed behavior;
- task-success changes;
- latency changes;
- retry behavior;
- recovery behavior;
- human-intervention requirements;
- repeated-observation instability;
- economic changes under comparable workloads.

The value of these patterns depends on explicit provenance and comparability.

---

## 46. Non-goals

DLLO methodology is not designed to produce:

- one global model score;
- one global agent score;
- an automatic universal winner;
- hidden baseline selection;
- undocumented provider-routing conclusions;
- inferred datacenter location;
- causal explanations without evidence;
- SUT self-certification.

The project favors explicit multidimensional evidence over a single opaque ranking.

---

## 47. Methodological checklist

Before presenting a DLLO result, ask:

```text
What exactly was observed?

Who or what provided each decision-relevant fact?

Which facts are OBSERVED?

Which are DECLARED?

Which are DERIVED?

Which remain UNKNOWN?

Was the SUT separated from verifier-only information?

Is the evaluation based on observer-owned evidence?

Is the relevant protocol or catalog version explicit?

Are the observations actually comparable?

Was baseline/candidate selection explicit?

Was geographic skew explicit?

Does region describe observation provenance rather than serving location?

Does the output describe observed change rather than unsupported cause?

Can the result be reconstructed from recorded evidence?
```

If one of these questions cannot be answered, the appropriate response is normally to expose the limitation rather than hide it.

---

## 48. Methodological principle

The methodology can be summarized as:

```text
MEASURE
What was actually observed?
        |
        v
PROVENANCE
Under which explicit conditions?
        |
        v
EVALUATE
What does the evidence establish?
        |
        v
COMPARE
Are the observations semantically compatible?
        |
        v
INTERPRET
What conclusions does the evidence actually support?
```

---

## Core principle

> **Observe first. Compare carefully. Explain only when the evidence allows it.**
