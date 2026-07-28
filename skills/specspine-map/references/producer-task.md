# SpecSpine Map one-shot producer contract

Handle exactly one bounded ToDo, write one checkpoint, and terminate only after
revising it to a checked atomic handoff. Inspect every packet `sample`, then read
only enough evidence to establish responsibility, interfaces, lifecycle, state,
dependencies, failures, and boundaries. This file is the complete producer
instruction set: do not load the Map `SKILL.md` or any other Map reference.
Start with targeted `rg` and narrow excerpts, target at most 10,000 output tokens per call, and never dump complete large files; exceed the target only for a concrete unresolved boundary.

Write Markdown only in staging; write checkpoint to `<work-package>/checkpoint.json`.
Do not edit the live Spine, repository source, tests, README, or campaign state;
do not write to handoff, continue to another unit, or integrate navigation.

## Mandatory preflight and handoff

Before handoff, reread every candidate as a coherent architectural
specification and verify:

- one canonical responsibility without duplicated neighboring ownership;
- observations remain `OBS`; every `Evidence:` span is a complete
  repository-relative path, never prefix-inherited shorthand;
- supported relevant boundaries, interfaces, state, lifecycle, failures, and
  relationships are present;
- semantic IDs are stable and links use the required complete labels;
- implementation inventory and unsupported intent are absent;
- every direction is a genuine unanswered architectural question.

Revise the private result until this review is clean. Then run exactly:

```text
python3 <producer-finalize-script> \
  <task-packet.json> <work-package> <handoff-package> \
  <repository-root> <spine-root>
```

The helper validates checkpoint shape and evidence samples, checks candidates
against the live Spine overlay, and atomically renames the entire work package.
If it reports findings, fix every candidate-caused finding and rerun it. Never
ask root to accept private work. Do not message root or any other agent; after
atomic handoff, report only in the producer's final response and terminate.

If available evidence cannot establish a clean result, remove draft Markdown
and return `retry` naming missing evidence. Use `blocked` only for a concrete
external dependency, not a draft defect. Root independently repeats all
acceptance checks; preflight never grants publication authority.

## Result

Write one small JSON object. Use only the fields shown below. `evidence` and
staged `OBS` paths are complete repository-relative concrete paths.
`directions` are plain questions; the campaign assigns their IDs and root
decides whether they become ToDo.
Existing owner:

```json
{
  "outcome": "covered",
  "evidence": ["pkg/services/caching/cache.go", "pkg/services/caching/service.go"],
  "summary": "The existing claims cover ownership, invalidation and fallback.",
  "owner": {
    "document": "caching.md",
    "claims": ["OBS-cache-lifecycle", "OBS-cache-failure-fallback"]
  },
  "directions": []
}
```

Missing observation:

```json
{
  "outcome": "draft",
  "evidence": ["pkg/services/caching/cache.go"],
  "summary": "No existing owner describes this cache lifecycle.",
  "directions": ["Who owns recovery after persistent invalidation failure?"]
}
```

For `draft`, place one or more publish-ready Markdown files under the work
package's `staging/` directory. Do not describe their paths or create/replace
operations in JSON; the preflight and `campaign.py` derive both from staging
and the live Spine.

Supporting implementation with no durable responsibility:

```json
{
  "outcome": "supporting",
  "evidence": ["pkg/cache/adapters/wire.go", "pkg/cache/adapters/options.go"],
  "summary": "The unit only wires options into the existing cache lifecycle.",
  "reason": "It introduces no owner, state, interface, lifecycle, or failure policy.",
  "directions": []
}
```

Use `supporting` only after checking every evidence stratum. It is not a
shortcut for an unclear boundary; use `retry` when ownership remains uncertain.

Insufficient evidence:

```json
{
  "outcome": "retry",
  "evidence": ["pkg/services/caching/cache.go"],
  "summary": "The adapter is visible but its persistent owner is not.",
  "need": ["pkg/storage/cache"]
}
```

External blocker:

```json
{
  "outcome": "blocked",
  "evidence": ["pkg/services/caching/cache.go"],
  "summary": "The repository delegates the contract to an unavailable schema.",
  "reason": "The external schema is required to determine ownership."
}
```

`draft`, `covered`, and `supporting` must cite at least one concrete member from
every evidence stratum. `covered` is valid only when the owner document exists,
every claim is a semantic ID in that document, the document references the unit
or inspected evidence, and the summary explains the boundary. A title or broad
neighboring owner is not proof.
