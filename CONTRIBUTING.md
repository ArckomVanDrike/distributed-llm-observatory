# Contributing to DLLO

Thank you for considering a contribution to **Distributed LLM Observatory (DLLO)**.

DLLO is an open-source framework for building evidence-based agent configurations, testing real AI agents, and producing reproducible observations of AI-system behavior.

Contributions are welcome in code, tests, documentation, benchmark design, reproducibility review, UI/UX, catalog data, and observation methodology.

---

## Project principles

Before contributing, please keep the core DLLO invariants in mind.

DLLO should preserve:

```text
Observation != explanation

System Under Test != Observer

Execution != Evidence

Evidence != Evaluation

Run artifact != Qualified observation

UNKNOWN != NOT_FEASIBLE

Private != Offline

Local execution != Offline capability
```

The project deliberately avoids:

- SUT self-certification;
- hidden latest selection;
- automatic baseline selection;
- automatic candidate selection;
- global model or agent scores;
- hidden geographic skew thresholds;
- inferred provider serving locations;
- unsupported causal claims;
- silent hard-constraint relaxation.

These are not merely style preferences. They are part of the DLLO methodology.

---

## Ways to contribute

Useful contributions include:

- bug fixes;
- regression tests;
- benchmark tasks;
- protocol improvements;
- Agent Starter decision cases;
- catalog entries;
- documentation improvements;
- UI/UX improvements;
- reproducibility checks;
- observation methodology review;
- new comparison cases;
- external agent integrations.

Opening an issue with a well-documented failure or questionable assumption is also valuable.

---

## Development setup

DLLO requires **Python 3.10+**.

Clone the repository:

```bash
git clone https://github.com/ArckomVanDrike/distributed-llm-observatory.git
cd distributed-llm-observatory
```

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run the Python test suite:

```bash
pytest
```

Run Ruff:

```bash
ruff check .
```

Check whitespace and patch integrity:

```bash
git diff --check
```

---

## Web collector development

The browser application lives in:

```text
web/collector/
```

Install dependencies:

```bash
cd web/collector
npm install
```

Run the browser-side tests:

```bash
npm test
```

Build the web application:

```bash
npm run build
```

Run the development server:

```bash
npm run dev
```

---

## Contribution workflow

Prefer focused changes with one clear purpose.

A typical development loop is:

```text
inspect
  |
  v
write or update a failing test when applicable
  |
  v
implement the smallest justified change
  |
  v
run targeted tests
  |
  v
run the complete relevant gate
  |
  v
review the diff
  |
  v
commit
```

Avoid unrelated refactors inside feature or bug-fix changes.

---

## Tests

Behavioral changes should normally include tests.

Tests are especially important when modifying:

- benchmark semantics;
- protocol behavior;
- observer/SUT boundaries;
- evidence provenance;
- comparison compatibility;
- artifact schemas;
- historical resolution;
- Agent Starter requirements;
- feasibility decisions;
- catalog matching;
- recommendation classification.

A change should not weaken an existing invariant merely to make a test pass.

---

## Agent Starter contributions

Agent Starter follows an explicit decision flow:

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

When contributing to Agent Starter:

- do not infer candidate properties from architecture IDs;
- do not turn UNKNOWN into failure without evidence;
- do not silently relax hard constraints;
- do not introduce hidden rankings;
- preserve multiple valid recommendations when appropriate;
- keep catalog snapshots explicit;
- keep user requirements separate from candidate properties.

---

## Observatory contributions

Observatory comparisons should answer:

> **What changed?**

They should not automatically answer:

> **Why did it change?**

Temporal and geographic comparisons must preserve explicit comparability rules.

Rejected comparison pairs should remain visible together with their rejection reasons.

Observation region means observation provenance.

It must not be interpreted as provider serving location.

---

## Consumer Probe contributions

Consumer Probe is intentionally human-in-the-loop.

Contributions must not introduce:

- automatic prompt submission;
- private-interface scraping;
- browser session-token collection;
- cookie collection;
- private provider endpoints;
- rate-limit bypass mechanisms.

---

## Documentation

Documentation changes are encouraged.

When documenting a capability, distinguish clearly between:

```text
implemented
planned
experimental
future
```

Do not present roadmap items as existing functionality.

Technical documentation should describe repository behavior as implemented.

---

## Pull requests

A good pull request should have:

- a focused purpose;
- a clear title;
- a short explanation of the change;
- relevant tests;
- no unrelated modifications;
- passing verification.

Before opening a pull request, run:

```bash
pytest
ruff check .
git diff --check
```

For changes affecting `web/collector/`, also run the relevant browser-side tests.

---

## Commit messages

Use concise, descriptive commit messages.

Examples:

```text
feat(agent-starter): add explicit offline evidence
fix(observatory): preserve rejected geographic pairs
test(agent-lab): cover recovery branch
docs: clarify observation provenance
refactor(agent-starter): separate catalog matching
```

---

## Compatibility and versioning

DLLO relies on explicit contracts.

Changes affecting:

- benchmark suites;
- protocol behavior;
- artifact schemas;
- catalog snapshots;
- comparison rules;

should consider whether a versioned contract must be preserved rather than silently changed.

Historical reproducibility takes precedence over convenience.

---

## Reporting methodological issues

If you believe DLLO is making an unsupported assumption, please open an issue.

Particularly useful reports include:

- hidden assumptions;
- non-reproducible behavior;
- ambiguous provenance;
- incorrect comparability;
- causal claims unsupported by evidence;
- benchmark leakage;
- verifier information exposed to the SUT;
- catalog decisions that rely on implicit properties.

Methodological criticism is welcome.

---

## License

By contributing to DLLO, you agree that your contribution will be distributed under the repository's **MIT License**.
