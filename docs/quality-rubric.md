# DLLO Quality Rubric

Distributed LLM Observatory (**DLLO**) defines a structured quality-evaluation contract for multidimensional assessment of AI responses.

The current contract is intentionally conservative.

It defines:

- which quality dimensions exist;
- the valid score range;
- provenance for the judge;
- consistency rules for the overall score.

It does **not** currently define universal semantic anchors for every integer value from 1 to 6.

DLLO therefore avoids pretending that a more precise rubric exists than the repository actually implements.

---

## 1. Purpose

Quality evaluation answers:

> How strong is this response across several distinct quality dimensions?

This is different from deterministic task evaluation.

```text
TaskEvaluation
      |
      v
Did the observed evidence satisfy
the explicit task criteria?

QualityEvaluation
      |
      v
How strong was the response
across multiple quality dimensions?
```

The two contracts should not be conflated.

---

## 2. Current quality dimensions

`QualityEvaluation` contains six component dimensions:

```text
fit
efficiency
clarity
style
structure
technical_accuracy
```

and one aggregate judgment:

```text
overall
```

Each score is an integer in the inclusive range:

```text
1 .. 6
```

---

## 3. Fit

`fit` represents the quality dimension named **fit** by the current schema.

The repository currently does not define a more detailed canonical 1–6 semantic scale for this dimension.

Therefore DLLO should not claim that a specific numeric value has a universal interpretation beyond the context of the judge contract that produced it.

---

## 4. Efficiency

`efficiency` represents the quality dimension named **efficiency** by the current schema.

The repository currently does not define universal semantic anchors for each score from 1 through 6.

Interpretation should therefore remain tied to the judge configuration and evaluation context.

---

## 5. Clarity

`clarity` represents the quality dimension named **clarity** by the current schema.

The current DLLO contract constrains its numeric range but does not yet publish a canonical semantic definition for every score value.

---

## 6. Style

`style` represents the quality dimension named **style** by the current schema.

The current repository does not establish a universal 1–6 style rubric.

A future rubric may introduce explicit anchors through a versioned contract.

---

## 7. Structure

`structure` represents the quality dimension named **structure** by the current schema.

As with the other dimensions, the current implementation defines its allowed numeric range but does not yet define a canonical semantic anchor for every integer score.

---

## 8. Technical accuracy

`technical_accuracy` represents the quality dimension named **technical accuracy** by the current schema.

The schema currently provides range validation and interaction with the `overall` consistency rules.

It does not yet define a universal textual interpretation for every possible value.

---

## 9. Overall

`overall` is a separate quality judgment.

It is not defined as:

```text
mean(dimensions)
```

and DLLO does not currently require it to be a mathematical average.

Instead, the schema constrains `overall` so that it cannot become obviously inconsistent with severe weaknesses or uniformly strong component scores.

---

## 10. Overall consistency rules

The current schema enforces three explicit invariants.

### Any dimension equals 1

If the minimum component score is:

```text
1
```

then:

```text
overall <= 2
```

Example:

```text
fit = 1
efficiency = 5
clarity = 5
style = 5
structure = 5
technical_accuracy = 5
```

An `overall` value of `3` or greater is invalid.

An `overall` value of `2` is structurally allowed.

---

### Any dimension equals 2

If the minimum component score is:

```text
2
```

then:

```text
overall <= 3
```

Example:

```text
clarity = 2
```

with:

```text
overall = 4
```

is invalid.

An `overall` value of `3` is structurally allowed.

---

### Every dimension is at least 4

If all six component dimensions satisfy:

```text
score >= 4
```

then:

```text
overall >= 4
```

For example:

```text
fit = 4
efficiency = 4
clarity = 4
style = 4
structure = 4
technical_accuracy = 4
overall = 3
```

is invalid.

An `overall` value of `4` is structurally allowed.

---

## 11. What these rules mean

These constraints prevent the aggregate quality judgment from contradicting obvious patterns in the component scores.

Conceptually:

```text
severe component weakness
        |
        v
cannot be hidden by high overall
```

and:

```text
uniformly solid component scores
        |
        v
cannot produce very low overall
```

The rules provide **consistency**, not a complete semantic scoring rubric.

---

## 12. What the current contract does not define

DLLO v0.1 does not currently define canonical universal statements such as:

```text
1 = unusable
2 = poor
3 = acceptable
4 = good
5 = excellent
6 = perfect
```

Those labels are **not** part of the current repository contract.

They must therefore not be presented as official DLLO methodology.

If explicit semantic anchors are introduced later, they should be:

- documented;
- versioned;
- tested;
- associated with the judge contract that uses them.

---

## 13. Judge provenance

Every `QualityEvaluation` records:

```text
judge_model
judge_version
```

Both are required non-empty strings.

This means a quality score is not represented as an anonymous fact.

It retains provenance about which judge configuration produced it.

---

## 14. Judge model

`judge_model` identifies the model or judging system responsible for the quality evaluation.

The field is required.

DLLO should preserve this value when storing or comparing quality judgments.

A score without judge provenance should not be silently treated as equivalent to one generated by a known judge configuration.

---

## 15. Judge version

`judge_version` records the version of the judging contract or implementation.

This allows future rubric or judge evolution without silently rewriting the meaning of historical evaluations.

Conceptually:

```text
quality score
    +
judge model
    +
judge version
    |
    v
reproducible judgment provenance
```

---

## 16. Judge agreement

`judge_agreement` is optional.

When present, it must satisfy:

```text
0 <= judge_agreement <= 1
```

The current schema does not impose a more specific interpretation or computation method.

Therefore DLLO should not claim that this field represents a particular statistical estimator unless the producing workflow explicitly defines one.

---

## 17. Human verification

The schema includes:

```text
human_verified: bool
```

with default:

```text
False
```

This field makes human verification explicit.

A machine-produced evaluation must not be represented as human-verified unless that status has actually been established.

---

## 18. Human verification does not rewrite provenance

Human verification is metadata about the evaluation.

It does not remove the need to retain:

```text
judge_model
judge_version
```

The originating judge remains part of the provenance of the quality record.

---

## 19. Quality evaluation vs task evaluation

DLLO defines a separate `TaskEvaluation` contract.

`TaskEvaluation` contains:

```text
task_id
method
criteria
passed
```

Each criterion contains:

```text
criterion
passed
evidence
```

The overall task result is Boolean:

```text
passed = True / False
```

---

## 20. Task evaluation methods

Current task evaluation methods are:

```text
DETERMINISTIC
HUMAN
```

represented as:

```text
deterministic
human
```

This contract answers whether explicit criteria passed.

It is separate from the multidimensional quality score.

---

## 21. Task result consistency

For `TaskEvaluation`, the overall Boolean result must exactly match the criterion results.

Conceptually:

```text
passed =
    every criterion passed
```

Therefore:

```text
one failed criterion
        |
        v
task passed = False
```

and:

```text
all criteria passed
        |
        v
task passed = True
```

A task cannot declare success while one of its explicit criteria failed.

---

## 22. Deterministic evidence has priority where available

When a task can be evaluated through explicit deterministic evidence, DLLO should prefer that evidence over replacing the task result with a subjective quality score.

For example:

```text
expected JSON structure
        |
        v
deterministic structural comparison
```

is conceptually different from asking:

```text
How good did the response feel?
```

Quality judgment should not erase deterministic correctness.

---

## 23. Quality does not replace correctness

A response may have:

```text
high clarity
high style
good structure
```

while still failing an explicit task criterion.

Conversely, a response may satisfy a deterministic criterion while receiving a weaker quality assessment in another dimension.

These are different observations.

DLLO preserves both when relevant.

---

## 24. No global model score

`overall` is **not** a global model score.

It represents the aggregate judgment inside one `QualityEvaluation`.

It must not silently become:

```text
model X = 5.2 globally
```

or:

```text
agent Y is universally better
```

without an explicitly defined aggregation methodology.

---

## 25. No global agent ranking

DLLO deliberately avoids collapsing heterogeneous tasks, environments, benchmark versions, and observation contexts into one hidden leaderboard score.

The existence of:

```text
overall
```

inside `QualityEvaluation` does not change that principle.

The relevant distinction is:

```text
response-level quality judgment
        !=
global target ranking
```

---

## 26. Comparability

Two quality evaluations should not automatically be treated as directly comparable merely because both contain numbers from 1 to 6.

Relevant provenance may include:

- judge model;
- judge version;
- task;
- benchmark;
- evaluation context;
- target;
- observation conditions.

A numeric scale alone is insufficient proof of semantic comparability.

---

## 27. Judge-version changes

If the judge definition changes meaningfully, historical scores should retain their original version.

DLLO should prefer:

```text
new judge behavior
        ->
new explicit judge version
```

rather than silently changing the interpretation of previously stored results.

---

## 28. Future semantic anchors

A future DLLO rubric may define explicit semantic anchors for the 1–6 scale.

If introduced, they should satisfy at least these requirements:

```text
explicit definitions
versioned contract
tests
judge provenance
dimension-specific interpretation
historical compatibility
```

Such anchors should not be added informally in documentation without corresponding implementation and versioning.

---

## 29. Future judge agreement semantics

Future workflows may define how `judge_agreement` is produced.

Possible mechanisms could involve multiple judges or comparison against a reference evaluator.

However, the current contract defines only:

```text
optional float in [0, 1]
```

No additional statistical meaning should be assumed today.

---

## 30. Current contract summary

The current quality contract is:

```text
QualityEvaluation

fit                 1..6
efficiency          1..6
clarity             1..6
style               1..6
structure           1..6
technical_accuracy  1..6
overall             1..6

judge_model         required
judge_version       required
judge_agreement     optional, 0..1
human_verified      bool, default False
```

with:

```text
if any dimension == 1
    overall <= 2

if any dimension == 2
    overall <= 3

if all dimensions >= 4
    overall >= 4
```

---

## 31. Interpretation rule

The safest interpretation of a current DLLO quality evaluation is:

> A multidimensional judgment produced by a named and versioned judge under the contract recorded with that evaluation.

It is **not**:

> An absolute universal score for the model or agent.

---

## 32. Contributor rule

Contributors changing quality semantics should not modify only prose.

Changes to scoring behavior should normally include:

- schema changes where required;
- tests;
- judge-version considerations;
- documentation updates;
- compatibility review.

If score semantics change, historical provenance must remain understandable.

---

## 33. Rubric checklist

Before consuming or publishing a `QualityEvaluation`, ask:

```text
Are all scores between 1 and 6?

Is judge_model explicit?

Is judge_version explicit?

Is judge_agreement present?
If so, is it between 0 and 1?

Was human verification actually performed?

Does overall satisfy the schema consistency rules?

Is this a quality judgment or a task PASS/FAIL result?

Are the judge versions comparable?

Am I accidentally treating overall as a global model score?

Am I assigning semantic labels that the current contract does not define?
```

---

## Core principle

> **Preserve multidimensional quality and judge provenance without pretending that a response-level score is a universal model ranking.**
