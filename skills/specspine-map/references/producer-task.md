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
- every staged owner has an evidence baseline and at least one v3 semantic
  `OBS` bullet; legacy `**ID:** ... **Status:**` definitions are invalid;
- supported relevant boundaries, interfaces, state, lifecycle, failures, and
  relationships are present;
- semantic IDs are stable and links use the required complete labels;
- implementation inventory and unsupported intent are absent;
- every direction is a genuine unanswered question; keep required policy
  distinct from observable repository behavior and never rewrite one as the
  other.

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

Use `covered` only for a source-pass inventory task. The cited claims must
cover the assigned production unit, not merely mention a neighboring concept.

For an integration-derived task, use `"outcome": "answered"` with the same
`evidence`, `summary`, `owner`, and `directions` fields only when cited claims
are all `OBS-*` and answer the exact observable anchored question. Repository
evidence cannot answer what the system should guarantee. Use `"outcome":
"unresolved"` with `evidence`, `summary`, `reason`, and empty `directions` when
evidence confirms the anchor must remain uncertain.

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

Use `"outcome": "supporting"` with `evidence`, `summary`, `reason`, and empty
`directions` only after every stratum proves the inventory unit has no durable
responsibility. Use `"outcome": "retry"` with `evidence`, `summary`, and
nonempty `need` when ownership remains unclear. Use `"outcome": "blocked"` with
`evidence`, `summary`, and `reason` only for a concrete external dependency.

`draft`, `covered`, `answered`, `unresolved`, and `supporting` must cite at
least one concrete member from every evidence stratum. `covered` is valid only
for inventory tasks; `answered` and `unresolved` are valid only for anchored
integration-derived tasks. For `covered` or `answered`, the owner document must
exist, every claim must be a semantic ID in it, the document must reference the
unit or inspected evidence, and the summary must explain the exact boundary or
answer. A title, unknown-owner observation, or broad neighboring owner is not
proof.
