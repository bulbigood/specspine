# SpecSpine Map one-shot producer contract

Handle exactly one bounded ToDo, write one checkpoint, and terminate. Read the
provided concrete source samples, candidate owner documents, and only enough
additional evidence to establish responsibility, interfaces, lifecycle, owned
state, dependencies, significant failures, and boundaries.

Write Markdown only under the assigned private staging root. Do not edit the
live Spine, repository source, tests, README, or campaign state. Do not continue
to another unit or integrate navigation.

## Result

Write one small JSON object. Use only the fields shown below. Paths in
`evidence` are repository-relative concrete files. `directions` are plain
questions; the campaign assigns their IDs and root decides whether they become
ToDo.

Existing owner:

```json
{
  "outcome": "covered",
  "evidence": [
    "pkg/services/caching/cache.go",
    "pkg/services/caching/service.go"
  ],
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

For `draft`, stage one or more publish-ready Markdown files. Do not describe
their paths or create/replace operations in JSON; `campaign.py` derives both
from staging and the live Spine.

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

`covered` is valid only when the owner document exists, every claim is a
semantic ID in that document, the document references the unit or inspected
evidence, and the summary explains the boundary. A title or broad neighboring
owner is not proof.
