# SpecSpine Map orchestration

Run every operation through one durable state machine:

```text
scope → discovery → synthesis → production → integration → verification
```

Only root runs `campaign.py`, edits the integration workspace, and publishes
the live Spine. Run `next-action` after every state transition.

## Start or resume

Before creating a campaign in a new session, inspect the private campaign home:

```text
python3 <skill>/scripts/campaign.py discover <campaign-home> <repository>
```

If it reports an incomplete campaign, require the operator to choose that exact
campaign or a new run. Resume only the selected ledger:

```text
python3 <skill>/scripts/campaign.py resume-session <campaign>
python3 <skill>/scripts/campaign.py next-action <campaign>
```

Resume preserves every `assigned` task so finalized atomic handoffs are not
lost. Before spawning producers, recover the interrupted wave:

```text
python3 <skill>/scripts/campaign.py harvest-wave \
  <campaign> <handoffs> <spine-root> <harvest-receipts>
```

Cached receipts are reusable. Release each `pending_task` and rejected task;
these have no acceptable atomic handoff and may be reassigned as a new attempt.
Do not release harvested tasks. After the releases, run `accept-wave` for the
remaining assigned tasks. If none remain, continue with `next-action`. Never
read or accept an unfinished producer work directory.

Otherwise create a unique private run directory and write `operation.json`:

```json
{
  "scope": {
    "kind": "semantic",
    "title": "Kafka and related services",
    "question": "Which components publish, consume, configure, deploy, observe, recover, or own Kafka contracts?",
    "inclusion_rule": "Include direct Kafka runtime, contract, operational, producer, and consumer responsibilities.",
    "exclusion_rule": "Exclude components connected only through shared infrastructure."
  },
  "completion": {"kind": "exhaustive"}
}
```

`scope.kind` is `semantic` or `repository`. Completion is
`{"kind":"exhaustive"}` or
`{"kind":"increment","intent":"survey|deepen|refresh|drift"}`. Repository
increment permits only `survey`.

```text
python3 <skill>/scripts/campaign.py init \
  <campaign> <operation.json> \
  --repository-root <repository> --spine-state <empty|existing>
```

For an existing Spine, record its exact v3 documents and checker baseline:

```text
python3 <skill>/scripts/campaign.py seed-from-spine \
  <campaign> <spine-root>
```

This seed grants no coverage. A non-v3 root is rejected.

## Discover

```text
python3 <skill>/scripts/campaign.py discovery-start \
  <campaign> <repository> <spine-root> <discovery>
```

Add `--inventory-accelerator` only for repository scope. The root packet and
neutral inventory pages form the initial discovery layer. Keep the default
page size; a page may never exceed the mechanical limit.

Set the scout subwave size to the smaller of ten and the runtime's available
subagent slots. If capacity includes root, reserve one slot. Do not assume ten
slots exist. For each selected packet, derive:

```text
<draft> = <private-scout-work>/<lead-id>/draft.json
<result> = <results>/<packet path relative to discovery>
```

Create at most that many fresh weak-tier scouts. Give each scout its packet,
repository, Spine, private draft path, exact result path, and
`discovery_finalize.py`:

```text
Read <skill>/references/discovery-task.md completely; it is your sole Map
contract. Analyze <packet> against <repository> and <spine-root>. Write the
semantic draft to <draft>, finalize it to <result> with
<skill>/scripts/discovery_finalize.py, and terminate only after it reports
ready.
```

Wait for the complete subwave without refill, then validate exactly its packet
list before trusting scout messages or starting more work:

```text
python3 <skill>/scripts/campaign.py discovery-validate \
  <discovery-seed> <discovery> <results> <packet>...
```

Any failure invalidates the subwave; repair or rerun it before continuing.
After all subwaves in a layer validate, give one fresh medium-tier curator the
operation, results, and compact lead registry under `frontier-curation.md`.

- Increment: disposition every unique in-scope continuation as `defer`; queue
  nothing.
- Exhaustive: queue every unique in-scope continuation; defer nothing.

Persist its decision and, for exhaustive work, execute the next layer:

```text
python3 <skill>/scripts/campaign.py discovery-packets \
  <discovery-seed> <frontier.json> <discovery>/wave-NNNN
```

Use the same adaptive scout limit, exact result paths, barrier, and validation
for every later layer. Safety limits establish blockage, never closure.

When the frontier is settled:

```text
python3 <skill>/scripts/campaign.py discovery-collect \
  <campaign> <discovery-seed> <discovery> <results> \
  <discovery-corpus.json>
```

## Synthesize

Give the complete corpus to one fresh medium-tier synthesizer under
`topic-synthesis.md`. It writes exactly `topics`, `covered`, `supporting`,
`open_leads`, and `deferred_leads`.

- Increment reproduces the corpus `deferred_leads` exactly and returns no
  `open_leads`.
- Exhaustive returns no `deferred_leads`. Reopen every `open_lead`, close the
  new frontier, collect again, and rerun whole-corpus synthesis:

```text
python3 <skill>/scripts/campaign.py discovery-reopen \
  <campaign> <discovery-seed> <topic-plan.json> \
  <discovery>/wave-NNNN
```

When synthesis is closed:

```text
python3 <skill>/scripts/campaign.py source-pass \
  <campaign> <repository> <spine-root> \
  --discovery-corpus <corpus.json> --topic-plan <topic-plan.json>
```

Only uncovered `topics` become producer tasks.

## Produce

For every `dispatch` action, create one strict wave:

```text
python3 <skill>/scripts/campaign.py ready <campaign> --limit 5
python3 <skill>/scripts/campaign.py packet \
  <campaign> <task-id> --output <packet.json>
python3 <skill>/scripts/campaign.py assign \
  <campaign> <task-id> --owner <fresh-producer-id>
```

Create fresh medium-tier producers. Give each only `producer-task.md`, its
packet, repository, Spine, private work/handoff paths, and
`producer_finalize.py`. Wait for the whole wave without refill. Producers
atomically expose checked handoffs; never inspect their work directories.

Harvest the complete wave, inspect receipts only after the barrier, then accept
or release tasks:

```text
python3 <skill>/scripts/campaign.py harvest-wave \
  <campaign> <handoffs> <spine-root> <harvest-receipts>
python3 <skill>/scripts/campaign.py accept-wave \
  <campaign> <handoffs> <spine-root> <harvest-receipts>
```

Acceptance validates evidence and staging but never publishes.

## Integrate

Read `integration-pass.md`. Create a private copy of the current Spine:

```text
python3 <skill>/scripts/campaign.py prepare-integration \
  <campaign> <spine-root> <workspace>
```

Resolve ownership and duplication, merge accepted drafts, update navigation and
manifest, disposition every task and suggestion, and write the required
integration report. Exhaustive integration may derive evidence-backed ToDo;
increment integration may not.

```text
python3 <skill>/scripts/campaign.py integration-pass \
  <campaign> <spine-root> <workspace> <report.json>
```

The command checks the complete workspace and publishes the workspace plus
ledger transition atomically. Repeat production and integration until
`next-action` returns `finalize`.

## Finish

Before every response:

```text
python3 <skill>/scripts/campaign.py next-action <campaign>
```

Follow its action: `discover`, `synthesize`, `dispatch`, `wait`, `integrate`,
`repair`, `finalize`, or `report_blocked`. `may_finish: false` forbids a normal
final answer. Pause only when `may_pause: true`.

Finalize only a verified terminal:

```text
python3 <skill>/scripts/finalize_run.py \
  <campaign> <spine-root> --staging-root <staging>
```

Report the operation, exact terminal claim, inspected evidence, deferred and
verified counts, changed Spine-relative paths, and unresolved uncertainty.
