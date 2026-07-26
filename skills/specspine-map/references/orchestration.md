# SpecSpine Map exhaustive orchestration

Exhaustive mode closes a deterministic repository inventory through independent
bounded ToDo tasks. It optimizes for visible state and fresh context, not
producer continuity.

## Invariants

- The root orchestrator is the only scheduler and the only process that runs
  `campaign.py`.
- One producer handles one ToDo, emits one checkpoint, and terminates.
- Never reuse a producer handle or send follow-up work into its conversation.
- Producers write only to private staging. They never edit the live Spine,
  `README.md`, source, tests, or campaign state.
- Producer suggestions are not ToDo items until the root integration pass
  accepts them.
- Producers do not score their own quality and cannot declare local or global
  saturation.
- Deterministic source inventory, persistent ToDo, and root integration are
  separate completion gates.
- Continue independent ready tasks after a producer failure. A tool failure is
  not an architectural blocker.
- Exhaustive mode requires fresh producer creation. Without it, preserve the
  inventory and report `blocked`.

Read [producer-task.md](producer-task.md) completely before dispatching work.

## Start

Create a private run root outside the repository and Spine:

```text
mktemp -d
python3 <map-skill-root>/scripts/campaign.py init \
  <run-root>/campaign.json \
  --scope <requested-scope> \
  --root-question <scope-question> \
  --spine-state existing
```

For an existing Spine, follow `documentation-first-seeding.md` before source
inventory. An empty Spine starts after the minimal index required by
`SKILL.md`.

Build the immutable producer bundle once:

```text
python3 <map-skill-root>/scripts/bundle_skill.py \
  <map-skill-root> <run-root>/producer-instructions.md
```

## Establish the source lower bound

Generate the deterministic area inventory:

```text
python3 <map-skill-root>/scripts/campaign.py inventory \
  <repository-root> --spine-root <spine-root>
```

The root classifies every returned area exactly once as:

- `mapped` or `neighbor-owned`, with an existing owner document;
- `queued`, with a matching ToDo;
- `generated`, `vendored`, `test-only`, or `no-architecture-value`, with a
  concrete reason.

Save the complete classification and new tasks:

```json
{
  "inventory": [
    {
      "area": "pkg/services/ssosettings",
      "classification": "queued",
      "task": "sso-settings",
      "reason": "Durable CRUD, persistence and reload boundary"
    },
    {
      "area": "vendor",
      "classification": "vendored",
      "reason": "Third-party source"
    }
  ],
  "todo": [
    {
      "id": "sso-settings",
      "question": "Who owns provider settings persistence and reload?",
      "reason": "The inventory exposes an independent service",
      "evidence": ["pkg/services/ssosettings"],
      "documents": ["identity-access.md"],
      "excludes": ["login orchestration"],
      "anchor": null
    }
  ],
  "terminal_reason": null
}
```

Record it:

```text
python3 <map-skill-root>/scripts/campaign.py source-pass \
  <campaign> <repository-root> <spine-root> <report.json>
```

The command rejects missing, duplicate, or invented inventory areas. An empty
source ToDo requires `no source-derived ToDo: <reason>`.

## Dispatch one-shot producers

Inspect ready work:

```text
python3 <map-skill-root>/scripts/campaign.py ready <campaign>
python3 <map-skill-root>/scripts/campaign.py todo <campaign>
```

For each safely available slot:

1. start a fresh producer with the immutable bundle and one task packet;
2. only after a producer handle exists, assign it:

```text
python3 <map-skill-root>/scripts/campaign.py assign \
  <campaign> <task-id> --owner <fresh-agent-path>
```

3. let it write private staging, return one checkpoint, and terminate;
4. root-inspect the checkpoint and staged candidates;
5. atomically publish an acceptable result:

```text
python3 <map-skill-root>/scripts/campaign.py accept \
  <campaign> <task-id> <checkpoint.json> \
  <private-staging-root> <spine-root> \
  --owner <fresh-agent-path>
```

`accept` validates staged bytes and the checkpoint, runs candidate and live
mechanical checks, publishes with rollback, records suggestions for integration,
and clears producer ownership. It never adds suggestions directly to ToDo.

If a producer disappears, use `release`; the same task returns to ToDo and must
be assigned to another fresh handle. A `needs_more_evidence` checkpoint also
returns the task to ToDo with its requested evidence. Never continue the old
producer.

## Integrate and derive ToDo

After any publications settle, perform the root-only integration contract in
`integration-pass.md`. The root rereads published documents and graph neighbors,
normalizes shared navigation and relationships, dispositions every producer
suggestion, and records every accepted or newly observed refinement as an
explicit ToDo.

The integration pass marks published tasks complete and atomically appends its
new ToDo items. Dispatch each with a fresh producer. Repeat:

```text
ToDo → fresh producer → staging → accept → integration → new ToDo
```

Do not let an empty ready list skip integration: published drafts may still
contain unresolved directions.

## Close the inventory

Run:

```text
python3 <map-skill-root>/scripts/campaign.py summary <campaign>
python3 <map-skill-root>/scripts/campaign.py coverage-report <campaign>
```

`inventory_closed` requires:

- no `todo`, `assigned`, `published`, or `blocked` task;
- every producer terminated;
- every publication and suggestion integrated;
- a current deterministic source inventory;
- a current integration pass that produced no further ToDo.

An empty ToDo is necessary but not sufficient. The campaign reports `partial`
until every gate passes. It reports `blocked` only when all actionable work is
drained and an explicit blocked task remains.

After `inventory_closed`, make no further documentation edits. Run the checker
and `finalize_run.py`. Report the inventory classifications, created/replaced
documents, integrated relationships, remaining uncertainty, and exact terminal
reasons. Recommend `$specspine-doctor` in a new session; never invoke it during
Map.
