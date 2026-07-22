# SpecSpine product hypothesis evaluation contract

## Product claim

Given the same documented repository, change request and coding agent, adding a
reviewed SpecSpine documentation graph should reduce architectural violations
without reducing functional correctness. The agent starts at the Spine index
and selects relevant documentation itself.

This claim is distinct from skill and Markdown-format regressions. Correct
links, semantic IDs and skill behavior do not establish downstream value.

## Experiment

Run all four task classes against the same frozen repository and request:

| Arm | Supplied context |
|---|---|
| `native-repository` | Complete repository with native documentation, tests, comments and configuration; no SpecSpine |
| `full-spine` | The identical repository plus the complete reviewed SpecSpine |

No task-specific context is preselected. The agent reads
`specspine/README.md` and navigates the graph itself.

## Controls

Use the same model, reasoning level, request, timeout, repository snapshot and
sample count in both arms. Keep the downstream prompt byte-identical; file
availability selects whether the agent uses native documentation or the Spine.
Do not expose the arm identifier through the environment. Verify the Spine arm
read its index from the trace.

Run every sample and judgment in a fresh restricted container from the same
content-addressed agent image. Reuse the immutable image, fixture archive and
preflight result, but never sample containers or runtime directories. Treat
image, sandbox, tool and metadata failures as invalid infrastructure rather
than product failures.

## Evaluation layers

Measure:

1. Mechanical outcome: executable behavior, syntax, required index read,
   workspace boundaries and context integrity.
2. Semantic outcome: requested behavior, preserved constraints, correct
   ownership, no duplicated responsibility and no invented blocking decision.
3. Context efficiency: unique and irrelevant files read, input tokens, elapsed
   time and reported cost.
4. Stability: variance and violation frequency across repeated samples.

Do not use exact response words, substring presence, file-count caps or guessed
change allowlists as proxies for meaning. A blind judge scores semantics from
only the request, diff, final response and frozen rubric. Overall pass requires
both mechanical and semantic pass. Calibrate the judge against human review
before treating a pilot as product evidence.

Archive the exact prompt, response, diff, trace, fixture/context hashes, image
identity and actual model settings for every run.

## Repository and tasks

The pilot uses hash-verified `hagopj13/node-express-boilerplate` commit
`179ae84efec61b14206d0305d941daed6c6d07f9` with all native documentation
preserved in both arms.

Task classes:

1. `local-utility`: architecture-neutral negative control.
2. `auditor-role`: cross-cutting authorization vocabulary.
3. `reset-revocation`: repository behavior conflicts with accepted token
   ownership.
4. `bootstrap-admin-policy`: safe implementation requires an unresolved
   security decision.

## Pilot budget and thresholds

The default pilot requires 4 tasks × 2 arms × 3 samples = 24 agent calls. Judge
every unique valid output requiring semantic review; identical judge inputs may
reuse one judgment.

Initial success thresholds for `full-spine` relative to `native-repository`:

- at least 30% fewer architectural violations across cross-cutting, conflict
  and blocking-policy tasks;
- no reduction in functional pass rate;
- at least 25% fewer task-irrelevant reads on architecture-significant tasks;
- no more than 15% higher median input-token use on the local negative control.

These are pilot thresholds, not universal product claims. Report every arm,
failure, model, reasoning level, prompt, sample count, duration and token
counter. Do not publish only aggregate wins.

## Interpretation

- If the Spine does not outperform native documentation, narrow or simplify
  the product.
- If gains appear only for architecture-significant changes, narrow the claim
  accordingly.
- If graph navigation is correct but expensive, simplify the index or links.
- If no stable gain appears, do not add formal graph or conformance machinery.
