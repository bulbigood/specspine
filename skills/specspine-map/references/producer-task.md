# SpecSpine Map one-shot producer contract

A producer handles exactly one bounded ToDo, emits one checkpoint, and
terminates. Inventory verification tasks contain one mechanically selected
repository work unit. Documentation- and integration-derived tasks may instead
contain an anchored architectural question.

The producer reads the task evidence, candidate owner documents, and only the
additional repository evidence needed to determine responsibility, interfaces,
lifecycle, dependencies, owned state, significant failures, and boundaries.
It writes Markdown only under its private staging root.

The producer does not:

- edit the live Spine, `README.md`, source, tests, or campaign state;
- continue to another work unit or discovered direction;
- add ToDo directly;
- accept a document title or broad owner as proof of coverage;
- decide repository completeness or integrate navigation.

## Task packet

```json
{
  "id": "verify-pkg-services-caching-9b8476c104",
  "question": "Verify whether repository unit pkg/services/caching is architecturally covered; publish the missing observation if it is not",
  "reason": "Every production-capable inventory unit requires an independent producer checkpoint",
  "evidence": ["pkg/services/caching"],
  "documents": ["grafana-system.md"],
  "excludes": [],
  "units": ["pkg/services/caching"],
  "anchor": null
}
```

`documents` are candidate owners discovered from literal repository-path
references. They are hypotheses, not authority.

## Checkpoint statuses

- `covered_by_owner`: an existing document explicitly accounts for the unit;
- `draft_ready`: staging contains a publish-ready create or replacement;
- `needs_more_evidence`: retry the same task with a fresh producer and the
  listed evidence;
- `blocked`: external authority or unavailable evidence prevents progress.

`covered_by_owner` is valid only when:

- `evidence_inspected` names at least one existing file inside every task unit;
- `owner_document` exists;
- every `owner_claim_ids` value exists as a semantic ID in that document;
- the owner document references the work unit or inspected source evidence;
- `boundary_summary` explains why the claim covers the unit.

Example:

```json
{
  "status": "covered_by_owner",
  "evidence_inspected": [
    "pkg/services/caching/cache.go",
    "pkg/services/caching/service.go"
  ],
  "findings": [
    "The service implements cache ownership, invalidation and fallback behavior"
  ],
  "candidates": [],
  "coverage": {
    "owner_document": "caching.md",
    "owner_claim_ids": ["OBS-cache-lifecycle", "OBS-cache-failure-fallback"],
    "boundary_summary": "The claims cover ownership, invalidation and failure fallback"
  },
  "discovered_directions": [],
  "required_evidence": [],
  "terminal_reason": null
}
```

For `draft_ready`, set `coverage` to `null` and list every staged candidate.
For `needs_more_evidence` and `blocked`, staging and discovered directions must
be empty.

Discovered directions are suggestions only. The root integration pass must
disposition each one and persist every accepted direction as ToDo.
