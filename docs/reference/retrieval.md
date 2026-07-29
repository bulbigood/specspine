# SpecSpine retrieval contract

## Goal

Extract returns the smallest deterministic specification closure for a task.
It reads only the SpecSpine root and requires no model or source-code access.

```text
query → candidates → canonical owner → typed closure → claims/assets → result
```

## Input

```json
{
  "id": "payment-retry-change",
  "targets": ["payment-processing"],
  "semantic_ids": [],
  "paths": [],
  "terms": [["retry", "repeated attempt"]],
  "facets": ["failure", "data-mutation"],
  "token_budget": 8000
}
```

Exact semantic ID, document ID, and path outrank title, alias, responsibility,
summary, and body matches. Query terms use the configured documentation
language. Exact project terms are never translated.

## Closure

- Always follow `superseded-by` and applicable `constrained-by`.
- Follow data relations for state or mutation work.
- Follow `exposes` for contracts and `consumes`/`publishes` for integrations.
- Use composition relations for selective zoom.
- Report incoming consumers and weak relations as potentially affected unless
  a stronger rule makes them required.

The result includes the primary owner, required and potentially affected
owners, applicable normative claims, registered assets, divergences, blockers,
observations and inferences as non-normative orientation, omissions, and
complete source files when budget permits.

## One status object

The result has exactly one top-level `status` object:

```json
{
  "status": {
    "code": "incomplete",
    "reason": "specification_facets_incomplete",
    "implementation_freedom": "contract-equivalent",
    "facets": {
      "architecture": "complete",
      "behavior": "complete",
      "interfaces": "partial",
      "data": "not-applicable",
      "failure": "complete",
      "quality": "partial",
      "verification": "missing"
    },
    "blockers": [],
    "requested_facets": ["data", "failure"],
    "incomplete_requested_facets": ["data"]
  }
}
```

Codes are `ready`, `incomplete`, `blocked`, `no-match`, `truncated`, and
`invalid`. The first three are computed from the selected manifest area.
Retrieval failures replace the computed area state. Status is never inferred
from prose labels.

A truncated result preserves the computed value as `status.area_code` and
preserves implementation freedom, requested facets, and blocking IDs even when
lower-priority details must be omitted.

`requested_facets` normalizes recognized query facets to the seven manifest
facets. `incomplete_requested_facets` lists requested facets whose aggregate
value is not `complete`. For an explicitly requested concern,
`not-applicable` is reported rather than silently treated as sufficient. This
task-specific signal does not replace or upgrade the whole-area status.

## Output

The result contains `status`, `primary`, `required`, `potentially_affected`,
all normative claim groups, `observations`, `inferences`, `assets`,
`known_divergences`, `blocking_questions`, `omitted`, and `sources`.

`observations` and `inferences` are orientation only. They never satisfy a
normative gap or establish conformance.

`concatenated_source_paths` names files returned in full.
`concatenated_files_omitted_paths` names exact files omitted by the budget.
Consumers do not reread returned files.

Truncation is explicit and never cuts a Markdown file inside the concatenated
payload. Missing information is reported rather than invented.
