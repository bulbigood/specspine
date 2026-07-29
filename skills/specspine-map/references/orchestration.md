# SpecSpine Map orchestration

Run every operation through one durable state machine:

```text
scope → discovery → synthesis → production → integration → verification
```

Only root runs `campaign.py`, edits the integration workspace, and publishes
the live Spine. Run `next-action` after every state transition.
## Start or resume

Use exactly `<workspace>/.specspine/map` as the campaign home. `campaign.py`
creates it and `<workspace>/.specspine/.gitignore` when absent. Never place Map
state elsewhere. Inspect it:

```text
python3 <skill>/scripts/campaign.py discover \
  <workspace>/.specspine/map <workspace>
```

If incomplete, resume that campaign. Select it with:

```text
python3 <skill>/scripts/campaign.py resume-session <campaign>
python3 <skill>/scripts/campaign.py recover <campaign> [existing-path options]
python3 <skill>/scripts/campaign.py next-action <campaign>
```
Path options: `--discovery-results`, `--synthesis-packet`, `--mapping`,
`--topic-plan`, `--handoffs-root`.
`recover` records supplied paths, validates results, and
returns missing/invalid work; later resumes use ledger paths. Discard AI drafts.

Resume preserves every `assigned` task so finalized atomic handoffs are not
lost. Before spawning producers, recover the interrupted wave:

```text
python3 <skill>/scripts/campaign.py settle-wave \
  <campaign> <handoffs> <spine-root> <harvest-receipts>
```

Cached receipts are reusable. Release each `pending_task`; it may be
reassigned. Repair only `rejected_tasks`, which represent mechanical handoff
failures. Never read or accept an unfinished producer work directory.

Do not create another campaign for the same incomplete operation. `init`
rejects that by default. Use its override only after an explicit operator
decision to abandon the preserved campaign, never as automatic recovery.
If an accepted `blocked` result is later proven to be a mechanical false
blocker, reopen only that task:

```text
python3 <skill>/scripts/campaign.py retry-blocked \
  <campaign> <task-id> --reason "<confirmed mechanical cause>"
```

The command preserves the prior attempt in task history and is idempotent.
It does not repeat discovery, synthesis, or accepted sibling tasks.

Otherwise create a unique run directory under
`<workspace>/.specspine/map/<run-name>/`. The campaign argument is always the
ledger file `<run>/campaign.json`, never the run directory or a sibling file.
Write the operation to `<run>/operation.json`:

Keep `campaign.json`, `operation.json`, discovery, synthesis, producer work,
handoffs, receipts, and integration work inside that run directory. Only
`<repository>` and `<spine-root>` name live project data.

```text
<run> = <workspace>/.specspine/map/<run-name>
<campaign> = <run>/campaign.json
```

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
  <run>/campaign.json <run>/operation.json \
  --repository-root <repository> --spine-state <empty|existing>
```

For an empty Spine, create its minimal v3 envelope idempotently before
discovery. Repeating this command creates only missing bootstrap files and
rejects unrelated existing content:

```text
python3 <skill>/scripts/campaign.py bootstrap-spine \
  <campaign> <spine-root> --project <stable-project-name>
```

For an existing Spine, record its exact v3 documents and checker baseline:

```text
python3 <skill>/scripts/campaign.py seed-from-spine \
  <campaign> <spine-root>
```

This seed grants no coverage. A non-v3 root is rejected.

## Discover

For semantic scope, estimate breadth from `operation.json`, the Spine root
`_INDEX.md`, and available runtime capacity; do not inspect production code
yet. Choose
one to ten independent semantic search boundaries: one or two for a narrow
mechanism, three or four for one service with dependencies, five to seven for
a subsystem, and eight to ten for a broad cross-cutting scope. Write:

```json
{
  "discovery_plan_version": 1,
  "rationale": "Kafka spans runtime, contract, integration, and operations.",
  "leads": [
    {
      "id": "consumer-lifecycle",
      "title": "Consumer lifecycle and recovery",
      "question": "Which owners start, stop, retry, and recover consumers?",
      "reason": "Runtime recovery is an independently searchable boundary."
    }
  ]
}
```

Each lead must be a distinct search lens, not a file group or duplicate
whole-scope pass. Desired lead count may exceed current capacity: capacity
controls subwaves, not discovery coverage.

```text
python3 <skill>/scripts/campaign.py discovery-start \
  <campaign> <repository> <spine-root> <discovery> \
  --initial-plan <initial-discovery-plan.json>
```

For repository scope, omit `--initial-plan` and add `--inventory-accelerator`.
The neutral inventory pages form the initial discovery layer; no whole-repository
root scout duplicates them. Keep the default
page size of 40 seed files; a scout packet or unresolved fallback may never
exceed that limit. This limit does not cap files found while closing the
packet's semantic boundary. The repository accelerator is exhaustive by
default.

Set the scout subwave size to the smaller of ten and the runtime's available
subagent slots. If capacity includes root, reserve one slot. Do not assume ten
slots exist. Dispatch every initial packet, in stable path order, across as
many strict subwaves as necessary. Never start frontier curation while an
initial packet is missing or invalid. For each packet in the next subwave,
derive:

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
After every initial packet validates, combine their `unresolved_leads` counts.
If the total is zero, collect the corpus immediately. Otherwise give
one fresh medium-tier curator the operation, unresolved proposals, and compact
lead registry under `frontier-curation.md`.

- Increment: disposition every unique in-scope continuation as `defer`; queue
  nothing.
- Exhaustive: queue every unique in-scope continuation; defer nothing.

Persist its decision and, for exhaustive work, execute only the targeted
fallback packets:

```text
python3 <skill>/scripts/campaign.py discovery-packets \
  <discovery-seed> <frontier.json> <discovery>/wave-NNNN
```

Every fallback scout uses the same closure contract, adaptive limit, exact
paths, barrier, and validation. Dispatch another wave only for justified
`unresolved_leads`. Never create mandatory breadth-first waves; safety limits
establish blockage, not closure.

When the frontier is settled:

```text
python3 <skill>/scripts/campaign.py discovery-collect \
  <campaign> <discovery-seed> <discovery> <results> \
  <discovery-corpus.json>
```
## Synthesize

Prepare one compact global packet from the complete corpus:

```text
python3 <skill>/scripts/synthesis.py prepare \
  <discovery-corpus.json> <synthesis-packet.json> --ledger <campaign>
```

Discovery packet/collect/reopen, synthesis prepare, and integration prepare
are input-digest-idempotent: reuse `already_ready`; never overwrite conflicts.

Give the packet to one fresh strong-tier synthesizer under
`topic-synthesis.md`. It writes a semantic mapping containing exactly
`topics`, `covered`, `supporting`, `open_leads`, and `deferred_leads`, with
`source_topic_ids` instead of files. Every semantic topic fixes its unique
canonical `document` and typed `relationships`; synthesis produces the future
Spine graph before production. The synthesizer first globally merges or
dispositions every source topic, then checks existing coverage and constructs
the graph; do not split either pass across isolated workers.

Materialize the synthesizer mapping directly to the campaign's sole canonical
`topic-plan.json`; never create `fixed`, `repaired`, or alternate plans:

```text
python3 <skill>/scripts/synthesis.py materialize \
  <discovery-corpus.json> <semantic-mapping.json> <campaign>/topic-plan.json
```

Never handwrite or repair `topic-plan.json`. Repair the semantic mapping and
rerun the deterministic commands. Closed materialization
validates a private temporary plan before atomically replacing the canonical
path; a plan containing open leads is only an atomic input to discovery reopen.
Record diagnostics such as `zero-existing-coverage`, `high-singleton-ratio`,
or `low-semantic-reduction`, but do not block production. Doctor or Evolve may
refine ownership and granularity later.

- Increment reproduces the corpus `deferred_leads` exactly and returns no
  `open_leads`.
- Exhaustive returns no `deferred_leads`. Reopen every `open_lead`, close the
  new frontier, collect again, and rerun whole-corpus synthesis:

```text
python3 <skill>/scripts/campaign.py discovery-reopen \
  <campaign> <discovery-seed> <topic-plan.json> \
  <discovery>/wave-NNNN
```

When the materialized synthesis is closed:

```text
python3 <skill>/scripts/campaign.py source-pass \
  <campaign> <repository> <spine-root> \
  --discovery-corpus <corpus.json> --topic-plan <topic-plan.json>
```

Only uncovered `topics` become producer tasks.
## Produce

For every `dispatch` action, create one strict resource wave:

```text
python3 <skill>/scripts/campaign.py ready <campaign> --limit 10
python3 <skill>/scripts/campaign.py packet \
  <campaign> <task-id> --output <packet.json>
python3 <skill>/scripts/campaign.py assign \
  <campaign> <task-id> --owner <fresh-producer-id> \
  --handoffs-root <wave-handoffs>
```

Use the exact `handoff_package` returned by `assign`; never construct or rename
the attempt suffix manually. Set the producer wave size to the smaller of ten
and available slots after reserving root. Create fresh strong-tier producers. Give each
only `producer-task.md`, its packet, repository, Spine, private work path,
that returned handoff path, and
`producer_finalize.py`. Wait for the whole wave without refill. Producers
atomically expose checked handoffs; never inspect their work directories.

Settle the complete wave with one idempotent command:

```text
python3 <skill>/scripts/campaign.py settle-wave \
  <campaign> <handoffs> <spine-root> <harvest-receipts>
```

It harvests and accepts every atomic handoff after the barrier. Mechanical
failures return `needs_mechanical_repair`; incomplete agents return
`waiting_for_handoffs`. Semantic doubts are notes, not rejection. Acceptance
validates evidence, checkpoint shape, digests, and path conflicts but does not
rerun the candidate checker already completed by `producer_finalize.py`.
The absence of an integration-owned `_INDEX.md` in a newly planned directory
is never a blocker; candidate checking defers that index to deterministic
assembly.
Immediately dispatch the next wave. Do not integrate between waves; continue
until every producer task is settled.
## Integrate

Run deterministic assembly:

```text
python3 <skill>/scripts/campaign.py assemble-integration \
  <campaign> <spine-root>
```

It requires all waves settled, enforces canonical producer paths, materializes
synthesized relationships, index navigation, conservative manifest facets, task
reviews, and the exact delta, then checks and publishes atomically. It owns the
campaign-local workspace and report paths; the orchestrator never creates,
reads, or edits them for a clean run. Repeat it after interruption; matching
inputs are idempotent. If it returns
`needs_semantic_review`, read `integration-pass.md` and use
`prepare-integration` plus `integration-pass` only for the reported ownership,
coverage, granularity, anchor, direction, or graph conflict. A producer
`covered` or `supporting` result contradicts the synthesized production plan
and is therefore an exception, not a routine review. Never manually review
clean drafts.
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
verified counts, changed Spine-relative paths, unresolved uncertainty, and the
receipt's reconstruction readiness. Say explicitly that `scope_verified`
means the selected repository-observation scope was completed; it does not
mean the Spine is reconstructable or that code conforms to it.
