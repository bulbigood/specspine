# SpecSpine Map exhaustive orchestration

Exhaustive mode verifies a mechanically generated repository frontier through
one-shot producers; root never classifies production code as already covered.

## Invariants

- Only root runs `campaign.py`.
- One fresh producer handles one ToDo and terminates after one checkpoint.
- Use a medium-capability general-purpose agent: `agent_type: medium` in Codex,
  or the middle multi-file-analysis tier elsewhere. Never use weak or strongest.
- Give every producer a fresh isolated context without inherited conversation or
  hidden memory (`fork_turns: none` in Codex). Pass only the command below.
- Producers write only to private staging.
- Root cannot create, remove, group, or terminally classify production units.
- A document is only a candidate owner until a producer supplies source evidence and existing semantic claim IDs.
- Producer suggestions enter ToDo only through root integration.
- Continue independent tasks after a producer failure.
- Dispatch strict waves; never refill a finished producer slot mid-wave.
- Without fresh producer creation, preserve generated ToDo and report `blocked`.

## Start

Create a durable private run root outside the repository, never an OS-temporary directory; ledger and staging must survive restarts and cleanup.

Follow `campaign-selection.md`. Create a unique run only when discovery returns
none or the operator chooses new. Never reuse a populated run or select by directory order. Continue an exact ledger identified by the current thread.

```text
mkdir -p <durable-private-run-root>
python3 <map-skill-root>/scripts/campaign.py init \
  <run-root>/campaign.json \
  --scope <requested-scope> \
  --root-question <scope-question> \
  --repository-root <repository-root> \
  --spine-state <empty-or-existing>
```

For an existing Spine, run the mechanical index from `documentation-first-seeding.md`.

Give each producer only this minimal launch command with resolved absolute paths:

```text
Handle exactly one exhaustive SpecSpine Map ToDo.
Contract: read <map-skill-root>/references/producer-task.md completely; it is
your sole Map contract. Do not read SKILL.md or any other Map reference.
Task: <task-packet.json>; roots: repository=<repository-root>; Spine=<spine-root>
Packages: work=<work-package>; handoff=<handoff-package>
Finalize script: <map-skill-root>/scripts/producer_finalize.py
Do not message other agents. Terminate after the atomic handoff.
```

Producers invoke neither `campaign.py` nor Doctor.

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

The command returns counts; the ledger retains the complete frontier. It:

- classifies concrete files before grouping;
- separates tests, fixtures, generated, vendored, documentation, governance,
  and local-support files from production;
- groups by concrete parent directory and never packs sibling subtrees;
- splits a flat directory over 80 files per file and requires one evidence
  obligation for every production file in each unit;
- creates one immutable verification ToDo for every remaining unit;
- finds candidate owner documents only through literal path references;
- records the complete source-content digest.

The source frontier is immutable. If repository content changes, discard the
private run and start from the new snapshot.

Candidate owners do not close work. There is no fallback owner and no root
classification equivalent to `mapped` or `neighbor-owned`.

`ready` orders work breadth-first: repository runtime and manifests,
composition/command entry points, top-level runtime families, leaf features,
then tooling. It round-robins peer families so an early large subtree cannot
precede the system skeleton. Integration refinement waits behind bootstrap work.

## Dispatch producer waves

At a wave boundary, use the smallest of ready ToDo, available producer slots,
and five:

```text
python3 <map-skill-root>/scripts/campaign.py ready <campaign> --limit <wave-size>
```

Use `todo --limit <n>` only for bounded diagnosis. For the selected wave:

1. Before spawning, prepare every packet and unique sibling work/handoff path:
   `<run-root>/producer-work/<task-id>-<attempt>` and `<run-root>/handoffs/<task-id>-<attempt>`; create only work's `staging/`:

```text
python3 <map-skill-root>/scripts/campaign.py packet <campaign> <task-id> --output <run-root>/packets/<task-id>-<attempt>.json
```

2. Require slots, precompute prompts, then emit all spawn calls back-to-back with
   no reasoning, status checks, assignments, waits, or other tools between them.
   Packet creation and spawning are one transaction; use batch spawn when
   available. In Codex use `agent_type: medium`, `fork_turns: none`.
3. After every handle returns, assign the whole wave:

```text
python3 <map-skill-root>/scripts/campaign.py assign <campaign> <task-id> \
  --owner <fresh-agent-path>
```

4. Whenever root wakes, inspect states, then harvest every available atomic handoff:

```text
python3 <map-skill-root>/scripts/campaign.py harvest-wave <campaign> <run-root>/handoffs <spine-root> <run-root>/harvest
```

The command derives all paths from the ledger; never construct or parse
shell-delimited task records. Harvest validates immutable
packages but must not mutate the ledger or live Spine. It reports invalid
handoffs without hiding valid siblings. Release rejected tasks after the
terminal barrier; preserve successfully harvested siblings.
5. If any producer remains live, wait without refill. Interrupt only after its
   predeclared deadline or an explicit irrecoverable stall; never invent a timeout
   after launch. After cancellation, preserve work, release it, and count it terminal.
6. after every wave member is completed, failed, or cancelled, accept or release
   the whole wave. Acceptance
   validates it and records private immutable results in one ledger transaction
   without writing the live Spine:

```text
python3 <map-skill-root>/scripts/campaign.py accept-wave <campaign> <run-root>/handoffs <spine-root> <run-root>/harvest
```

Only an atomically renamed handoff may be harvested. Do not inspect or accept
`producer-work`. A missing terminal handoff is a failed attempt: preserve work
and release the task. Root reruns checks; never trust the producer receipt. A failed spawn remains ready
in the smaller wave and is not refilled; elapsed time alone is not failure.

`draft` remains private and waits for root integration. Source-pass `covered`
and `supporting` also wait for root review. Integration-derived `answered`
means existing claims answer the exact anchored question; `unresolved` means
the uncertainty remains real. Acceptance checks task/outcome compatibility,
every evidence stratum, owner existence, and semantic claim IDs. `retry`
returns the task to ToDo immediately. Never continue the old producer.

If a producer disappears, use `release`. If a fresh isolated producer or the
medium-capability tier is unavailable, use `block` for every actionable task
and report the campaign blocked. Never fall back to a weak or strongest tier.

## Integrate and derive ToDo

After the wave settles, follow `integration-pass.md`: prepare one private
workspace, review drafts and receipts, disposition every anchor and suggestion,
then publish the checked workspace as one transaction. Never edit live Spine
between acceptance and integration. After integration, immediately tell the
operator what it established and list every changed Spine-relative Markdown
path. Repeat cumulative document history in every progress or final summary.

Repeat:

```text
ToDo → producer wave → barrier → batch acceptance → one integration → new ToDo
```

An empty ready list does not skip integration: tasks may be waiting in
`published` or `review`. `published` means a private accepted draft, not a live
document.

## Turn continuity

The durable campaign is the unit of completion; a model turn is only an
execution slice. Time, tokens, compaction, a settled wave, an empty slot, or a
large remaining count never authorizes stopping.

At campaign start, after every integration pass, after every resumed turn, and
before any final answer, run:

```text
python3 <map-skill-root>/scripts/campaign.py next-action <campaign>
```

Follow its `action`:

- `dispatch` — start one bounded wave in a single assistant action;
- `wait` — wait for the entire assigned wave without refill;
- `integrate` — perform the root integration pass before dispatching more;
- `repair` — restore current source/integration evidence without inventing
  coverage;
- `finalize` — run `finalize_run.py`;
- `report_blocked` — report the concrete protocol blocker.

`may_finish: false` forbids a final answer. Send progress only in commentary,
then act in the same turn. Do not phrase progress as a handoff, yield control,
ask for “continue”, or obey hints. The operator must not have to restart.

`may_finish: true` is necessary but not sufficient for success:

- for `finalize`, require `finalize_run.py` to succeed with a clean
  repository-aware v3 result; repair remaining baseline defects first;
- for `report_blocked`, finish only with the exact blocker and preserved ledger.

After infrastructure interruption, use the exact ledger named in the thread,
run `next-action`, and continue. Never select by directory ordering.

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
- source and live Spine hashes are current, the v3 checker is clean, and the
  latest integration pass produced no ToDo.

This status means every inventory work unit was verified under this protocol;
it is not a claim that no conceivable architectural concept exists.

After `inventory_verified`, make no further edits. Run `finalize_run.py`,
report classifications, verification counts, publications and uncertainty, and
recommend `$specspine-doctor` in a separate session.
