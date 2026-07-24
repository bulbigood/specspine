# Scenario: rolling large-Map orchestration with two worker slots

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
independent starting questions and keep both slots occupied while undispatched
starting questions remain. A completed producer must free a slot for the next
ready starting question before its staging output is consumed.

Continue every evidence-backed follow-up until Map can add no useful
architectural document. Each of the six branches requires a terminal depth
probe after its useful document, so the run has at least twelve producer tasks
while only two may run concurrently.

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
slot from the four undispatched starting questions without a batch barrier.
It may inspect the repository and existing Spine as needed to understand the
requested scope, while producers own deep evidence investigation. Producers
stop after writing and reporting; the consumer alone validates and publishes
candidates. Because the fixture contains no material deeper nodes, reports
should not add new architectural branches. After publishing the six useful
documents, one terminal depth probe per branch should create nothing and report
`no useful node`. The orchestrator then normalizes once and removes the
successful disposable run root.

## Failure indicators

- fewer than six useful assignments or six terminal probes are dispatched;
- more than two producers are active;
- a worker slot remains idle while an undispatched starting question is ready;
- the orchestrator consumes completed staging before refilling an available
  slot from the initial queue;
- one producer receives more than one architectural zone;
- producer prompts omit the inline mapping contract or tell workers to load it;
- source or tests change;
- the disposable run root remains after success.
