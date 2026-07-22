# SpecSpine product hypothesis evaluation contract

## Product claim

Given the same documented repository, change request, and coding agent, a
reviewed SpecSpine handoff should reduce architectural violations and
irrelevant repository exploration relative to the repository's native
documentation without reducing functional correctness. For
architecture-significant changes, a minimal handoff should provide at least as
much downstream value as navigating the full Spine at lower context cost.

This claim is distinct from skill and format regressions. Correct Markdown,
valid links, stable semantic IDs, and compliant skill behavior do not establish
downstream value.

## Focused experiments

Do not run every possible context strategy in one benchmark. Each experiment
answers one product question with the smallest sufficient set of arms.

### Incremental value

Run all four task classes against the same frozen repository and request.

| Arm | Supplied context |
|---|---|
| `native-repository` | Complete repository with its native README, API documentation, tests, comments, and configuration; no SpecSpine |
| `minimal-handoff` | The same repository plus a reviewed handoff and only its required specifications |

This is the primary product comparison. It measures incremental value over a
normally documented project, not over an artificial code-only repository.

### Projection efficiency

Run only architecture-significant tasks.

| Arm | Supplied context |
|---|---|
| `full-spine` | Native repository plus the complete reviewed SpecSpine; no handoff |
| `minimal-handoff` | Native repository plus a reviewed handoff and only its required specifications |

This is a design ablation for the handoff mechanism, not a general product
baseline. Run it when handoff selection or format materially changes.

### Handoff production

Give `specspine-grow` the complete frozen Spine and the same request. Compare
its returned handoff with a human-reviewed reference. The producer must not
inspect repository material outside the Spine. No implementation is performed.

## Experimental controls

Do not let one arm see files assigned to another arm. Use the same model,
reasoning level, request, timeout, repository snapshot, and sample count within
each experiment. Keep the complete downstream prompt byte-identical. Its common
routing rule uses `HANDOFF.md` when present, otherwise the full Spine index when
present, otherwise native documentation. Thus file availability selects the
path without naming the arm or adding an instruction confound. Do not expose the
arm identifier through the environment. Verify required handoff/index reads
from the trace.

The value and projection experiments reuse the same task definitions so their
requests and deterministic outcome checks cannot drift. Arms from different
experiments are never interpreted as a direct comparison.

## Two evaluation layers

### Handoff production

Evaluate a generated handoff against a human-reviewed reference set:

- canonical primary owner;
- required specification recall and precision;
- potentially affected versus merely related classification;
- preservation of relevant decisions, constraints, and blocking questions;
- absence of feature requirements, tasks, and implementation proposals;
- files read and input tokens.

Do not require exact prose or ordering.

### Downstream outcome

Use frozen, human-reviewed context in the value and projection experiments.
Evaluate automatic handoff production separately so producer failure is not
confused with downstream consumer failure.

Measure:

1. Mechanical outcome: executable behavior, syntax, required context reads,
   workspace boundaries, context integrity, and objectively required no-change
   outcomes.
2. Semantic outcome: requested behavior that cannot be executed cheaply,
   preserved constraints, correct ownership boundary,
   no duplicated responsibility, and no silently invented blocking decision.
3. Context efficiency: unique files read, task-irrelevant files read, input
   tokens, elapsed time, and reported cost when available.
4. Stability: variance and violation frequency across repeated samples.

Do not use exact words, substring presence, file-count caps, or guessed change
allowlists as proxies for meaning. A blind judge scores remaining implementation
semantics against a task rubric and must not know which arm produced the result.
Handoff production uses a separate handoff rubric and must never be penalized
for its required empty diff. Overall pass requires both mechanical and semantic
pass. Calibrate rubric and judge behavior against human review before treating a
pilot as product evidence.

Archive the exact prompt, response, diff, trace, fixture/context hashes, and
actual model settings for every run. Construct judge inputs from only the
request, diff, final response, and frozen scenario rubric. Keep arm and
experiment metadata outside that bundle.

## Benchmark repository and tasks

The pilot uses a hash-verified archive of
`hagopj13/node-express-boilerplate` at commit
`179ae84efec61b14206d0305d941daed6c6d07f9`. Its frozen native README,
Swagger documentation, tests, comments, and configuration remain available in
every downstream arm.

Task classes:

1. `local-utility` — architecture-neutral negative control; handoff overhead
   should be negligible.
2. `auditor-role` — cross-cutting authorization change with one canonical role
   vocabulary.
3. `reset-revocation` — repository behavior conflicts with accepted token
   ownership.
4. `bootstrap-admin-policy` — safe implementation requires an unresolved
   security decision.

Include architecture-neutral tasks. A framework that only helps deliberately
favorable cases has not established general value.

## Pilot execution budget

The default manifests require 36 agent calls:

- value: 4 tasks × 2 arms × 3 samples = 24;
- projection: 2 tasks × 2 arms × 2 samples = 8;
- handoff production: 4 tasks × 1 sample = 4.

Run the value experiment regularly. Run projection only after material changes
to handoff format or selection. Judge every unique comparative output requiring
semantic review; identical judge inputs reuse one judgment.

## Pilot success criteria

Set thresholds before the main run. Initial thresholds for `minimal-handoff`
relative to `native-repository` are:

- at least 30% fewer architectural violations across cross-cutting, conflict,
  and blocking-policy tasks;
- no reduction in functional pass rate;
- at least 25% fewer task-irrelevant file reads on architecture-significant
  tasks;
- no more than 15% higher median input-token use on the local negative control.

For projection, require no reduction in functional or architectural pass rate
and lower median input-token use for `minimal-handoff` relative to `full-spine`.

Treat these as pilot decision thresholds, not universal performance claims.
Report every arm, failed sample, model identifier, reasoning level, prompt,
sample count, duration, and token counter. Do not publish only aggregate wins.

## Interpretation

- If SpecSpine does not outperform native repository documentation, narrow or
  simplify the product.
- If the full Spine helps but the handoff does not, revise handoff selection.
- If only the handoff helps, keep it as the primary interoperability surface.
- If gains occur only for architecture-significant changes, narrow the product
  claim accordingly.
- If handoff production fails while reviewed handoffs help downstream work,
  improve the producer without changing the consumer contract.
- If no stable gain appears, do not add formal graph or conformance machinery.
