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
  equivalent. Pass only the minimal launch command below.
- Producers write only to private staging.
- Root cannot create, remove, group, or terminally classify production work
  units.
- An existing document is only a candidate owner until a producer supplies
  concrete source evidence and existing semantic claim IDs.
- Producer suggestions enter ToDo only through root integration.
- Continue independent tasks after a producer failure.
- Dispatch strict waves; never refill a finished producer slot mid-wave.
- Without fresh producer creation, preserve generated ToDo and report
  `blocked`.

## Start

Create a durable private run root outside the repository. Do not use an
OS-temporary directory for an exhaustive campaign: the ledger and staging must
survive thread restarts and machine cleanup.

Follow `campaign-selection.md` before initialization in a new session. Use a
new uniquely named run root only after discovery returns none or the operator
chooses new. Never reuse a populated run directory or select by directory
order. If the current thread already identifies its exact ledger, continue it.

```text
mkdir -p <durable-private-run-root>
python3 <map-skill-root>/scripts/campaign.py init \
  <run-root>/campaign.json \
  --scope <requested-scope> \
  --root-question <scope-question> \
  --repository-root <repository-root> \
  --spine-state <empty-or-existing>
```

For an existing Spine, run the mechanical index from
`documentation-first-seeding.md`.

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

On resume, ignore any legacy generated instruction artifact in the run root; it
is not required by the ledger. Producers invoke neither `campaign.py` nor Doctor.

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

The command returns counts, never the full generated ToDo list. The ledger retains the complete frontier. It:

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

## Dispatch producer waves

At a wave boundary, set the wave size to the smaller of ready ToDo and available producer slots. Inspect only that bounded slice:

```text
python3 <map-skill-root>/scripts/campaign.py ready <campaign> --limit <wave-size>
```

Use `todo --limit <n>` only for bounded diagnosis. For the selected wave:

1. before spawning, prepare every packet and unique sibling work/handoff path: `<run-root>/producer-work/<task-id>-<attempt>` and
   `<run-root>/handoffs/<task-id>-<attempt>`; create only work's `staging/`:

```text
python3 <map-skill-root>/scripts/campaign.py packet <campaign> <task-id> --output <run-root>/packets/<task-id>-<attempt>.json
```

2. precompute every launch prompt, then emit all spawn calls back-to-back with no reasoning, status checks, assignments, waits, or other tools between them.
   Use a platform batch-spawn operation when available. For Codex use `agent_type: medium`, `fork_turns: none`, and the minimal command above;
3. after every handle is returned, assign the whole wave:

```text
python3 <map-skill-root>/scripts/campaign.py assign <campaign> <task-id> \
  --owner <fresh-agent-path>
```

4. whenever root wakes, inspect producer states, then harvest every available atomic handoff in one read-only command while others continue:

```text
python3 <map-skill-root>/scripts/campaign.py harvest-wave <campaign> <run-root>/handoffs <spine-root> <run-root>/harvest
```

The command derives task, attempt, owner, handoff, and receipt paths from the ledger; never construct or parse shell-delimited task records. Harvest may
validate and review immutable packages and prepare integration decisions, but must not mutate the ledger or live Spine.
5. if any producer remains live, wait again without refill. Interrupt only when its predeclared deadline expired or the platform explicitly reports an
   irrecoverable stall; never invent a timeout after launch. After confirmed cancellation, preserve its work, release its task, and count it terminal.
6. after every wave member is completed, failed, or cancelled, accept or release the whole wave, then perform one integration pass:

```text
python3 <map-skill-root>/scripts/campaign.py accept-wave <campaign> <run-root>/handoffs <spine-root> <run-root>/harvest
```

Only an atomically renamed handoff may be harvested. Do not inspect or accept `producer-work`. Missing handoff after termination is a failed attempt: preserve work
for diagnosis and release the task. Root reruns candidate and post-publication checks; never trust the producer receipt as acceptance proof. A failed spawn remains ready
in the smaller wave and is not refilled; elapsed time without a predeclared deadline or explicit stall is not failure.

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

After the entire wave settles, follow `integration-pass.md`. Root reviews published drafts and `covered` receipts, dispositions every suggestion, updates
navigation or relationships, and atomically appends newly exposed questions to ToDo. After each producer document is successfully integrated, root immediately
tells the operator in commentary what the integration established or corrected
and lists every created or changed Spine-relative Markdown path. Do not batch
these per-document write notifications into the final summary.

Repeat:

```text
ToDo → producer wave → barrier → batch acceptance → one integration → new ToDo
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
