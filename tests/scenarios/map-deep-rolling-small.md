# Scenario: branch-affine deep-Map orchestration with two worker slots

## Existing SpecSpine

The live Spine contains only its runtime composition. Six small, independent
runtime-adjacent responsibilities remain unmapped.

## User request

```text
Use `$specspine-map-deep` to map identity sessions, background job execution,
telemetry export, notification delivery, search indexing, and webhook ingestion
as deeply as repository evidence supports. The environment provides individual
completion and exactly two safe mapping-worker slots in addition to the
orchestrator. Never have more than two producers active. Treat the six areas as
independent starting branches. Assign each branch to one producer session and
never reuse that session for another area. Keep both slots occupied whenever
ready work can run without violating branch affinity.

After a producer returns its useful checkpoint, preflight and publish it, then
resume that same producer session with the compact instruction `Continue the
same architectural branch to terminal depth; do not reload or repeat immutable
instructions.` The resumed turn must create nothing and report `no useful
node`. Thus the run creates exactly six producer sessions and resumes each at
least once while only two sessions may run concurrently. Producers may propose
independent fork candidates, but only the orchestrator may accept and schedule
them; this fixture contains none.

Use `.specspine-map-run/` as the disposable run root and a unique private path
under `.specspine-map-run/staging/` for every producer. Give producers complete
self-contained text commands; they must not load skills or mapping references.
There are no other material coverage gaps or deeper architectural nodes in this
fixture. The harness configures producer models outside their commands. Keep
the resulting Spine flat; it does not justify namespace directories. Every
useful document must cite its area’s source, test, and configuration evidence
under their actual repository-relative paths. Use
`.eval/tools/check_spine.py` for candidate preflight. Discover the requested
scope adaptively; do not create a survey manifest, ledger, or recovery state.
Build the producer bundle with exactly:
`python3 .eval/skill/scripts/bundle_skill.py
.eval/companions/specspine-map
.specspine-map-run/producer-instructions.md --print`.
Publish the useful zones as `identity-sessions.md`,
`background-job-execution.md`, `telemetry-export.md`,
`notification-delivery.md`, `search-indexing.md`, and
`webhook-ingestion.md`. Existing `runtime.md` is the relevant overview for
these runtime-adjacent zones; use producer reports to add reciprocal navigation
from it without rereading the new documents. Do not run SpecSpine Doctor.
```

## Expected behavior

The orchestrator should start exactly two producers, then refill every freed
slot from the four undispatched starting branches without a batch barrier.
It may inspect the repository and existing Spine as needed to understand the
requested scope, while producers own deep evidence investigation. Producers
pause after writing and reporting; the consumer alone validates and publishes
candidates. It then resumes the same session for that branch without resending
the Map bundle. Because the fixture contains no material deeper nodes, no fork
candidate should be accepted. Each resumed session reaches terminal `no useful
node`, after which its slot can be assigned to another branch. The orchestrator
then normalizes once and removes the successful disposable run root.

## Failure indicators

- other than six producer sessions are created;
- any branch lacks a same-session terminal continuation;
- more than two producers are active;
- a producer session is reused for a different architectural area;
- a terminal continuation repeats the Map bundle or immutable shared context;
- one producer receives more than one architectural zone;
- producer prompts omit the inline mapping contract or tell workers to load it;
- any checker finding is bypassed or a candidate is moved after nonzero preflight;
- the final report omits the literal terminal phrase `no useful node`;
- source or tests change;
- the disposable run root remains after success.
