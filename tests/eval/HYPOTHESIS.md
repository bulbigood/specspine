# SpecSpine product hypothesis evaluation contract

## Product claim

Given the same repository, change request, and coding agent, relevant SpecSpine
context should reduce architectural violations and irrelevant repository
exploration without reducing functional correctness. A minimal context handoff
should provide at least as much downstream value as navigating the full Spine
at lower context cost.

This claim is distinct from skill and format regressions. Correct Markdown,
valid links, stable semantic IDs, and compliant skill behavior do not establish
downstream value.

## Comparison arms

Run every downstream benchmark against the same frozen repository and request.

| Arm | Supplied architectural context | Question answered |
|---|---|---|
| `repository-only` | none | What does the coding agent achieve unaided? |
| `architecture-document` | a token-budgeted conventional `ARCHITECTURE.md` | Is any architecture document sufficient? |
| `full-spine` | the complete frozen SpecSpine | Does linked architectural memory improve navigation? |
| `minimal-handoff` | a reviewed handoff and only its required specifications | Does task-scoped projection retain value at lower cost? |

Do not let one arm see files assigned to another arm. Use the same model,
reasoning level, request, timeout, repository snapshot, and sample count.
Use one byte-identical downstream prompt that does not name the arm or context
format. Do not expose the arm identifier through the agent environment.

## Two evaluation layers

### Handoff production

Evaluate a generated handoff against a human-reviewed reference set:

- canonical primary owner;
- required specification recall;
- required specification precision;
- potentially affected versus merely related classification;
- preservation of relevant decisions, constraints, and blocking questions;
- absence of feature requirements, tasks, and implementation proposals;
- files read and input tokens.

Do not require exact prose or ordering.

### Downstream outcome

Use frozen, human-reviewed context in the comparison arms before evaluating
automatic handoff production. This separates producer failure from downstream
consumer failure.

Measure:

1. Functional outcome: build, tests, and requested observable behavior.
2. Architectural outcome: preserved constraints, correct ownership boundary,
   no duplicated responsibility, and no silently invented blocking decision.
3. Context efficiency: unique files read, irrelevant files read, input tokens,
   elapsed time, and reported cost when available.
4. Stability: variance and violation frequency across repeated samples.

Deterministic checks own build and observable behavior. A blind judge may score
architectural outcomes, but must be calibrated against human review and must
not know which comparison arm produced the result.

Archive the exact prompt, response, diff, trace, fixture/context hashes, and
actual model settings for every run. Construct judge inputs separately from
only the request, diff, and frozen scenario rubric. Keep arm metadata outside
that bundle.

## Initial scenarios

1. `local-change` — one canonical owner; additional context should add little
   overhead.
2. `cross-cutting-change` — several architectural responsibilities are relevant.
3. `intended-observed-conflict` — repository behavior disagrees with an accepted
   constraint.
4. `blocking-question` — safe implementation requires an unresolved policy
   decision.

Include tasks where architectural context is irrelevant. A framework that only
helps carefully selected favorable cases has not established general value.

## Pilot success criteria

Set thresholds before the main run. Initial thresholds for the
`minimal-handoff` arm relative to `repository-only` are:

- at least 30% fewer architectural violations across cross-cutting and conflict
  scenarios;
- no reduction in functional pass rate;
- at least 25% fewer irrelevant file reads;
- no more than 15% higher median input-token use on local changes.

Treat these as pilot decision thresholds, not universal performance claims.
Report every arm, failed sample, model identifier, reasoning level, prompt,
sample count, duration, and token counters. Do not publish only aggregate wins.

## Interpretation

- If SpecSpine does not outperform `ARCHITECTURE.md`, simplify the product.
- If the full Spine helps but the handoff does not, revise handoff selection.
- If only the handoff helps, make it the primary interoperability surface.
- If gains occur only for architecture-significant changes, narrow the product
  claim to those changes.
- If no stable gain appears, do not add formal graph or conformance machinery.
