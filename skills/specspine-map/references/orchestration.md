# SpecSpine Map exhaustive orchestration

Exhaustive mode verifies a mechanically generated repository frontier through
independent one-shot producers. Root schedules and integrates; it does not
classify production code as already covered.

## Invariants

- Only root runs `campaign.py`.
- One fresh producer handles one ToDo and terminates after one checkpoint.
- Use a medium-capability general-purpose agent for every producer. Do not use
  the platform's weak/cheap tier or strongest/premium tier. In Codex select
  `agent_type: medium`; elsewhere select the closest middle tier intended for
  bounded multi-file code analysis and synthesis.
- Give every producer a fresh isolated context with no inherited conversation,
  reasoning, or hidden memory. `fork_turns: none` is the Codex spelling; on
  another platform create a new independent session or use its no-history
  equivalent. Pass only the immutable bundle, task packet, and required paths.
- Producers write only to private staging.
- Root cannot create, remove, group, or terminally classify production work
  units.
- An existing document is only a candidate owner until a producer supplies
  concrete source evidence and existing semantic claim IDs.
- Producer suggestions enter ToDo only through root integration.
- Continue independent tasks after a producer failure.
- Without fresh producer creation, preserve generated ToDo and report
  `blocked`.

Read [producer-task.md](producer-task.md) completely before dispatch.

## Start

Create a durable private run root outside the repository. Do not use an
OS-temporary directory for an exhaustive campaign: the ledger and staging must
survive thread restarts and machine cleanup.

Use a new uniquely named run root for every campaign. Never reuse a directory
that already contains `campaign.json`, checkpoints, staging, integration
reports, or other campaign artifacts. Old run roots are inert unless selected
explicitly, so resolve and pass the exact intended ledger path instead of
discovering or selecting a campaign by directory order.

Before initializing, inspect the current thread for an exact campaign ledger
created for this request. If one exists, resume it; never create a replacement
campaign merely because execution entered a new turn or context was compacted.

```text
mkdir -p <durable-private-run-root>
python3 <map-skill-root>/scripts/campaign.py init \
  <run-root>/campaign.json \
  --scope <requested-scope> \
  --root-question <scope-question> \
  --spine-state <empty-or-existing>
```

For an existing Spine, run the mechanical documentation index from
`documentation-first-seeding.md`.

Build the immutable producer bundle once:

```text
python3 <map-skill-root>/scripts/bundle_skill.py \
  <map-skill-root> <run-root>/producer-instructions.md
```

## Generate the source frontier

Inspect the deterministic inventory if useful:

```text
python3 <map-skill-root>/scripts/campaign.py inventory \
  <repository-root> --spine-root <spine-root>
```

Then record it without an AI-authored classification report:

```text
python3 <map-skill-root>/scripts/campaign.py source-pass \
  <campaign> <repository-root> <spine-root>
```

The command:

- classifies concrete files before grouping;
- separates nested tests, fixtures, generated files, vendored dependencies,
  documentation, governance, and local support from production;
- groups production files by stable repository boundaries and splits oversized
  units by subdirectory before deterministic fallback chunks;
- limits every production unit to 80 concrete files;
- records up to four evidence strata spanning each production unit;
- creates one immutable verification ToDo for every remaining unit;
- finds candidate owner documents only through literal path references;
- records the complete source-content digest.

The recorded source frontier is immutable. If repository content changes before
completion, discard the private run and start a new campaign from the new
snapshot.

Candidate owners do not close work. There is no fallback owner and no root
classification equivalent to `mapped` or `neighbor-owned`.

## Dispatch producers

Inspect ready work:

```text
python3 <map-skill-root>/scripts/campaign.py ready <campaign>
python3 <map-skill-root>/scripts/campaign.py todo <campaign>
```

For every available slot:

1. start a medium-capability producer in a fresh isolated session; for Codex
   use `agent_type: medium` and `fork_turns: none`; pass the immutable bundle
   and one task packet including all evidence-stratum samples;
2. after the handle exists, assign it:

```text
python3 <map-skill-root>/scripts/campaign.py assign \
  <campaign> <task-id> --owner <fresh-agent-path>
```

3. accept its single checkpoint:

```text
python3 <map-skill-root>/scripts/campaign.py accept \
  <campaign> <task-id> <checkpoint.json> \
  <private-staging-root> <spine-root> \
  --owner <fresh-agent-path>
```

`draft` is transactionally published and waits for root integration. `covered`
also waits for root integration; acceptance checks every evidence stratum,
owner existence, and semantic claim IDs. `supporting` records a producer-owned
finding that the unit has no durable architectural responsibility; root may
confirm it or return it to ToDo. `retry` returns the task to ToDo immediately.
Never continue the old producer.

If a producer disappears, use `release`. If a fresh isolated producer or the
medium-capability tier is unavailable, use `block` for every actionable task
and report the campaign blocked. Never fall back to a weak or strongest tier.

## Integrate and derive ToDo

After results settle, follow `integration-pass.md`. Root reviews both published
drafts and `covered` receipts, dispositions every suggestion, updates
navigation or relationships, and atomically appends newly exposed questions to
ToDo.

Repeat:

```text
ToDo → fresh producer → one checkpoint → root integration → new ToDo
```

An empty ready list does not skip integration: tasks may be waiting in
`published` or `review`.

## Turn continuity

The durable campaign is the unit of completion. A model turn is only an
execution slice. Elapsed time, token use, context compaction, a settled wave,
an empty producer slot, or a large remaining count never authorizes stopping.

At campaign start, after every integration pass, after every resumed turn, and
before any final answer, run:

```text
python3 <map-skill-root>/scripts/campaign.py next-action <campaign>
```

Follow its `action`:

- `dispatch` — fill every available producer slot from `ready`;
- `wait` — wait for assigned producers, then accept or release them;
- `integrate` — perform the root integration pass before dispatching more;
- `repair` — restore current source/integration evidence without inventing
  coverage;
- `finalize` — run `finalize_run.py`;
- `report_blocked` — report the concrete protocol blocker.

`may_finish: false` forbids a final answer. Send progress counts only through
the platform's intermediate/commentary channel and immediately continue the
returned action. Do not phrase progress as a handoff, ask the operator to say
“continue”, or treat a platform turn-duration hint as task completion.

`may_finish: true` is necessary but not sufficient for success:

- for `finalize`, finish only after `finalize_run.py` succeeds;
- for `report_blocked`, finish only with the exact blocker and preserved ledger.

If execution is resumed after an infrastructure interruption, use the exact
ledger path already reported in the thread, run `next-action`, and continue
from that state. Never infer the newest campaign by directory ordering.

## Verify the inventory

Run:

```text
python3 <map-skill-root>/scripts/campaign.py summary <campaign>
python3 <map-skill-root>/scripts/campaign.py coverage-report <campaign>
```

`inventory_verified` requires:

- every mechanically queued inventory unit has a completed producer result;
- no `todo`, `assigned`, `review`, `published`, or `blocked` task;
- every producer terminated;
- every result and suggestion was integrated;
- source and live SpecSpine hashes still match the verified snapshots;
- the latest integration pass produced no ToDo.

This status means every inventory work unit was verified under this protocol;
it is not a claim that no conceivable architectural concept exists.

After `inventory_verified`, make no further edits. Run `finalize_run.py`,
report classifications, verification counts, publications and uncertainty, and
recommend `$specspine-doctor` in a separate session.
