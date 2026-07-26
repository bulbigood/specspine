# SpecSpine Map exhaustive orchestration

Exhaustive mode verifies a mechanically generated repository frontier through
independent one-shot producers. Root schedules and integrates; it does not
classify production code as already covered.

## Invariants

- Only root runs `campaign.py`.
- One fresh producer handles one ToDo and terminates after one checkpoint.
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

```text
mkdir -p <durable-private-run-root>
python3 <map-skill-root>/scripts/campaign.py init \
  <run-root>/campaign.json \
  --scope <requested-scope> \
  --root-question <scope-question> \
  --spine-state <empty-or-existing>
```

For an existing Spine, run the complete documentation seed from
`documentation-first-seeding.md`. This seed may add anchored ToDo but cannot
remove later source-verification work.

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

- groups files into stable repository work units;
- deterministically splits every unit to at most 200 concrete files;
- mechanically excludes only vendored dependency trees, generated/build
  outputs, repository-level test trees, governance documents, and known local
  editor/contributor support;
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

1. start a fresh producer with the immutable bundle and one task packet;
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

`draft` is transactionally published and waits for root integration.
`covered` also waits for root integration; acceptance checks concrete unit
evidence, owner existence, and semantic claim IDs. `retry` returns the task to
ToDo for a new producer. Never continue the old producer.

If a producer disappears, use `release`. If fresh producer creation is
unavailable, use `block` for every actionable task and report the campaign
blocked.

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
