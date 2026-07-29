# Root integration and ToDo derivation

Use this manual pass only when `assemble-integration` reports semantic
exceptions. Clean producer drafts are assembled directly from the synthesized
graph plan. Acceptance proves checkpoint shape and evidence references; this
fallback resolves only reported ownership, direction, conflict, or graph
disagreement.

## Integrate publications

Create one private workspace first:

```text
python3 <map-skill-root>/scripts/campaign.py prepare-integration \
  <campaign> <spine-root> <integration-workspace>
```

The root orchestrator must:

1. Read every private draft and `covered`, `answered`, `unresolved`, or
   `supporting` receipt, its claimed owner, and relevant graph neighbors.
2. Confirm or correct ownership, boundaries, terminology, and non-duplication.
   Treat `architecture_unit` as a synthesized topic, not a required document
   path. Correct its final ownership when evidence demands it; never publish a
   models/utils/services document merely because the repository has that
   directory.
3. Add navigation needed for reachability and comprehension.
4. Add architectural edges through canonical `Relationships` tables; never add
   reciprocal rows only for navigation.
5. Use semantic IDs as complete link labels when targeting statements.
6. Preserve one canonical definition and ask before choosing among materially
   different plausible owners.
7. Inspect every producer direction. Queue only repository-observable questions;
   preserve required policy verbatim in its canonical document.
8. Disposition the originating anchor of every integration-derived task as
   `resolved`, `refined`, `still-open`, or `blocking`. Remove a resolved
   question; never leave stale uncertainty beside its answer. Reread the
   integrated documents for narrower unanswered mechanisms,
   transitions, failures, ownership questions, and consequences.
9. Update `specspine.json` in the same batch: add or remove area entries with
    their owners, set only evidence-supported facets, preserve normative facets
    and blockers, and register no asset a producer did not publish and own.
    Retain the exact campaign-supplied evidence baseline in every integrated
    source publication; do not invent `repository`, `no-git`, or path-shaped
    baseline values.
10. For exhaustive completion, append every accepted repository-observable
    refinement to persistent ToDo. For increment completion, never queue
    derived ToDo; cover, preserve, or reject directions because adjacent work
    is already recorded in `deferred_leads`.
11. Run the full checker on the workspace. The campaign supplies its recorded repository
    root. An existing-Spine campaign may retain an exact seed-baseline finding
    temporarily, but every new finding rejects integration. Remove applicable
    baseline defects while integrating their owners; finalization accepts none.
12. After the whole integration transaction and its checks succeed, send an
    immediate commentary update: say what was established, name every affected
    Spine-relative Markdown path, and label it `created`, `changed`, or `deleted`.
    Never announce a write before publication succeeds.
13. Repeat cumulative path-and-operation history in every progress or final
    summary. If no Spine file changed, explicitly say so.

The root edits only the integration workspace, including `README.md` and
`specspine.json`. Producers may not edit the index or manifest. The live Spine
must remain unchanged until `integration-pass` publishes the checked workspace.

## Report

Save a report whose `evidence_inspected` names only workspace Markdown
documents actually read during this integration. The command inventories and
checks the complete workspace independently; do not copy the full inventory into this
field unless every document was read:

```json
{
  "evidence_inspected": ["README.md", "identity.md", "sessions.md"],
  "changed_documents": [
    {"path": "identity.md", "operation": "changed"},
    {"path": "sessions.md", "operation": "created"}
  ],
  "task_reviews": [
    {"task": "identity-sessions", "disposition": "integrated",
     "reason": "The new owner and consumes edge are canonical",
     "anchor_disposition": {"status": "resolved",
       "reason": "The integrated owner replaces the original question"}}
  ],
  "suggestion_reviews": [
    {"task": "identity-sessions", "suggestion": "session-refresh-race",
     "disposition": "queued", "todo": "session-refresh-race",
     "reason": "The lifecycle exposes unresolved recovery ownership"}
  ],
  "todo": [
    {
      "id": "session-refresh-race", "basis": "repository-observation",
      "question": "Who owns recovery when refresh races with expiry?",
      "reason": "The integrated lifecycle establishes normal expiry only",
      "evidence": ["src/sessions", "tests/session-refresh.test.ts"],
      "documents": ["sessions.md"],
      "excludes": ["login", "token issuance"],
      "anchor": {"document": "sessions.md", "location": "Lifecycle / refresh transition",
        "known": "Normal expiry is documented", "question": "Who owns recovery when refresh races with expiry?"}
    }
  ],
  "organization": {"status": "flat_sufficient", "reason": "Owners remain directly navigable"},
  "terminal_reason": null
}
```

`changed_documents` is the exact workspace delta since the preceding
successful integration pass (or source pass for the first integration). The
command rejects missing, extra, or mislabeled paths, verifies that live Spine
still matches the preceding snapshot, and returns the published delta.

Every task in `published` or `review` needs one `task_reviews` row. A private
draft requires `integrated`; source-pass `covered` requires
`already_canonical`; integration-derived `answered` requires
`answered_canonical`; `unresolved` requires `still_open`; and `supporting`
requires `confirmed_supporting` or `retry`. `retry` returns that unit to ToDo
for a fresh producer.

Every non-retried task with an anchor needs `anchor_disposition`:

- `resolved` — remove the exact question after integrating its answer;
- `refined` — replace it with a narrower persistent ToDo and name its ID in
  `anchor_disposition.todo`;
- `still-open` — preserve the uncertainty with a concrete reason;
- `blocking` — name its semantic ID in `anchor_disposition.blocker`, define that
  `OQ-*` in the anchor owner, and add it to the owner's manifest area.

Root cannot independently mark a queued source unit non-architectural.
`confirmed_supporting` is valid only for a producer `supporting` receipt.
Integration fails if a published owner was deleted, lacks semantic `OBS`,
loses source evidence, or has no incoming or outgoing typed relationship.
Correct a poor draft in place; do not terminally discard it.

Every suggestion emitted by those tasks needs one `suggestion_reviews` row.
Allowed dispositions are:

- `queued`, with a matching `todo`;
- `covered`, when the integrated graph already answers it;
- `preserved`, with a document containing the exact normative question;
- `rejected`, with a concrete architectural reason.

Increment completion forbids `queued`; its report must contain an empty `todo`.

The root may add ToDo that no producer suggested. Every Map ToDo uses basis
`repository-observation` and exactly matches visible `anchor.question`; never
convert required policy into an observable question.
If `todo` is empty, use:

```text
no integration-derived ToDo: <evidence-based reason>
```

Record and verify:

```text
python3 <map-skill-root>/scripts/campaign.py integration-pass \
  <campaign> <spine-root> <integration-workspace> <integration-report.json>
```

The command checks the complete workspace, mechanical validity, settled-task
reviews, anchor and suggestion dispositions, and ToDo references. It publishes
the workspace and advances the ledger as one rollback-protected operation. Any
later producer result invalidates the pass.
