# Root integration and ToDo derivation

Run this pass after producer results settle and once more before campaign
closure. Acceptance proves checkpoint shape and evidence references, not
canonical ownership or complete architectural depth.

## Integrate publications

The root orchestrator must:

1. Read every published document or `covered` receipt, its claimed
   owner, and relevant graph neighbors.
2. Confirm or correct ownership, boundaries, terminology, and non-duplication.
3. Add navigation needed for reachability and comprehension.
4. Add architectural edges through canonical `Relationships` tables; never add
   reciprocal rows only for navigation.
5. Use semantic IDs as complete link labels when targeting statements.
6. Preserve one canonical definition and ask before choosing among materially
   different plausible owners.
7. Inspect every producer-discovered direction.
8. Reread the integrated documents for narrower unanswered mechanisms,
   transitions, failures, ownership questions, and consequences.
9. Append every accepted refinement to persistent ToDo. Do not investigate it
   during integration.
10. Run the full live checker.

The root may edit live specifications and `README.md`. Producers may not.

## Report

Save a report covering every live Markdown document:

```json
{
  "evidence_inspected": ["README.md", "identity.md", "sessions.md"],
  "task_reviews": [
    {
      "task": "identity-sessions",
      "disposition": "integrated",
      "reason": "The new owner and consumes edge are canonical"
    }
  ],
  "suggestion_reviews": [
    {
      "task": "identity-sessions",
      "suggestion": "session-refresh-race",
      "disposition": "queued",
      "todo": "session-refresh-race",
      "reason": "The integrated lifecycle exposes unresolved recovery ownership"
    }
  ],
  "todo": [
    {
      "id": "session-refresh-race",
      "question": "Who owns recovery when refresh races with expiry?",
      "reason": "The integrated lifecycle establishes normal expiry only",
      "evidence": ["src/sessions", "tests/session-refresh.test.ts"],
      "documents": ["sessions.md"],
      "excludes": ["login", "token issuance"],
      "anchor": {
        "document": "sessions.md",
        "location": "Lifecycle / refresh transition",
        "known": "Normal refresh and expiry are documented"
      }
    }
  ],
  "organization": {
    "status": "flat_sufficient",
    "reason": "The owner set remains directly navigable"
  },
  "terminal_reason": null
}
```

Every task in `published` or `review` needs one `task_reviews` row. A published
draft requires `integrated`; a `covered` receipt requires
`already_canonical`; a `supporting` receipt requires `confirmed_supporting` or
`retry`. `retry` returns that unit to ToDo for a fresh producer.

Root cannot independently mark a queued source unit non-architectural.
`confirmed_supporting` is valid only for a producer `supporting` receipt.
Integration fails if a published owner was deleted, lacks a semantic `OBS`
claim, or no longer references the verified unit or its source evidence.
Correct a poor draft in place; do not terminally discard it.

Every suggestion emitted by those tasks needs one `suggestion_reviews` row.
Allowed dispositions are:

- `queued`, with a matching `todo`;
- `covered`, when the integrated graph already answers it;
- `rejected`, with a concrete architectural reason.

The root may add ToDo that no producer suggested. Each task still needs a
document anchor when documentation-derived. If `todo` is empty, use:

```text
no integration-derived ToDo: <evidence-based reason>
```

Record and verify:

```text
python3 <map-skill-root>/scripts/campaign.py integration-pass \
  <campaign> <spine-root> <integration-report.json>
```

The command checks the complete Markdown inventory, mechanical validity,
settled-task reviews, suggestion dispositions, and ToDo references. It marks
reviewed results complete and appends ToDo atomically. Any later producer result
invalidates the pass.
