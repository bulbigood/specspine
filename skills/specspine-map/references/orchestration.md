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
python3 <skill>/scripts/campaign.py status <campaign>
python3 <skill>/scripts/campaign.py next-action <campaign>
```
Every completed phase or worker handoff has a valid `_receipt.json` or sidecar
`.<name>.receipt.json`, written last with input and output digests. Receipts are
the source of truth; the ledger does not duplicate artifact paths or digests.
`status` derives recovery state from receipts and settles an interrupted Spine
publication. Discard work without a valid receipt.

Assigned producer tasks remain assigned across interruption. Before spawning
replacement producers, settle the interrupted wave:

```text
python3 <skill>/scripts/campaign.py settle-wave \
  <campaign> <handoffs> <spine-root> <harvest-receipts>
```

Cached harvest receipts and finalized handoffs are reusable. Release each
`pending_task`; it may be
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

Prepare a compact packet for one isolated semantic planner:

```text
python3 <skill>/scripts/planning.py prepare \
  <campaign> <repository> <spine-root> <planner-packet.json>
```

Give one fresh medium-tier planner only `discovery-planner.md`, the packet,
repository, Spine, private draft path, final plan path, and `planning.py`.
The planner may inspect topology and narrow code excerpts; root must not read
production code, the draft, or the plan. It returns only a receipt with the
validated lead count and digest. Use the same plan path for every scope:

```text
python3 <skill>/scripts/planning.py finalize \
  <planner-packet.json> <private-draft.json> <initial-plan.json>
python3 <skill>/scripts/campaign.py discovery-start \
  <campaign> <repository> <spine-root> <discovery> \
  --initial-plan <initial-plan.json>
```

Every lead is a semantic search boundary. Repository scope uses the same
pipeline; never partition it into mandatory file pages. Capacity controls
subwaves, not discovery coverage. A scout packet or unresolved fallback may
contain at most 40 seed files, but the scout may find more while closing its
semantic boundary.

The logical scout wave may contain at most ten packets, but run at most five
weak-tier scouts concurrently and never exceed the runtime's available
subagent slots. If capacity includes root, reserve one slot. Dispatch initial
packets in stable path order across strict cohorts. A capacity failure gets one
fresh weak-tier replacement after the current cohort settles. Record every
capacity failure immediately:

```text
python3 <skill>/scripts/campaign.py discovery-capacity \
  <campaign> <packet>
```

The first failure returns `retryable`; the second capacity failure is a
platform blocker and returns `platform_blocked`.
Do not substitute a more expensive model or retry again in the same run.
`next-action` then permits a platform-boundary pause and reports the exact
completed, pending, retryable, and blocked packets. On a later explicit
operator continuation after capacity may have recovered, reopen only those
blocked packets:

```text
python3 <skill>/scripts/campaign.py discovery-resume-capacity <campaign>
```

This preserves completed results and lifetime failure counts. Never synthesize
while an initial packet is missing or invalid. `discovery-start` and
`discovery-packets` return canonical `assignments` containing exact `packet`
and `result` paths. Use both paths verbatim; never prefix, rewrite, or derive
the result path. Derive only the private draft path:

```text
<draft> = <private-scout-work>/<lead-id>/draft.json
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

Any invalid result blocks the cohort until repaired. After every initial packet
validates, deterministically defer every unresolved continuation without
another scout wave:

```text
python3 <skill>/scripts/campaign.py discovery-defer \
  <discovery-seed> <discovery> <results> <discovery>/deferred
```

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
  <discovery-corpus.json> <synthesis-packet.json>
```

Discovery packet/collect, synthesis prepare, and integration prepare are
input-digest-idempotent: reuse `already_ready`; never overwrite conflicts.

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
rerun the deterministic commands. Materialization validates a private
temporary plan before atomically replacing the canonical path. For exhaustive
work it converts residual `open_leads` into `deferred_leads`; it never reopens
discovery automatically.
Record diagnostics such as `zero-existing-coverage`, `high-singleton-ratio`,
or `low-semantic-reduction`, but do not block production. Doctor or Evolve may
refine ownership and granularity later.

- Increment reproduces the corpus `deferred_leads` exactly and returns no
  `open_leads`.
- Exhaustive performs one global synthesis. Materialization retains every
  residual open lead as deferred work and continues to production.

When the materialized synthesis is closed:

For whole-repository exhaustive work only, audit the synthesized topology
before production:

```text
python3 <skill>/scripts/coverage.py prepare \
  <corpus.json> <topic-plan.json> <coverage-packet.json>
```

Give one fresh medium-tier auditor only `repository-coverage.md`, the packet,
repository, Spine, private draft path, final review path, and `coverage.py`.
Root reads only its receipt. Finalize the review:

```text
python3 <skill>/scripts/coverage.py finalize \
  <coverage-packet.json> <private-draft.json> <coverage-review.json>
```

On `gaps`, reopen the reported semantic leads, run the ordinary scout,
collection, and synthesis loop, then audit again:

```text
python3 <skill>/scripts/campaign.py coverage-reopen \
  <campaign> <discovery-seed> <coverage-review.json> \
  <discovery>/coverage-NNNN
```

Only a recorded `clear` review for the current topic plan permits
whole-repository exhaustive production. Other scopes skip this audit.

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
and available slots after reserving root. Create fresh medium-tier producers. Give each
only `producer-task.md`, its packet, repository, Spine, private work path,
that returned handoff path, and
`producer_finalize.py`. Wait for the whole wave without refill. Producers
receive compact SpecSpine authority and format semantics inside their sole
contract; never make them infer keyword authority from an example draft.
Packets include compact existing and planned neighbor responsibilities so
parallel production preserves synthesized ownership boundaries.
atomically expose checked handoffs and write `_receipt.json` last; never
inspect their work directories.

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

It requires all waves settled, enforces canonical producer paths and owner
IDs, materializes
synthesized relationships, index navigation, conservative manifest facets, task
reviews, and the exact delta, then checks and publishes atomically. It owns the
campaign-local workspace and report paths; the orchestrator never creates,
reads, or edits them for a clean run. Repeat it after interruption; matching
inputs are idempotent. Publication uses a transaction journal; `status`,
`next-action`, or the next integration command commits a completed swap or
restores the recorded backup after interruption. Only an explicit
`needs_semantic_review` status authorizes semantic integration. A command error
or mechanical rejection does not: repair the named producer artifact and rerun
deterministic assembly. Never use `integration-pass` to repair identity, paths,
baselines, relationship rendering, manifest areas, indexes, or changed-file
bookkeeping. When assembly returns `needs_semantic_review`, read
`integration-pass.md` and use
`prepare-integration` plus `integration-pass` only for the reported ownership,
coverage, granularity, anchor, direction, or graph conflict. A producer
`covered` or `supporting` result contradicts the synthesized production plan
and is therefore an exception, not a routine review. Never manually review
clean drafts.
## Finish

Before every response:

```text
python3 <skill>/scripts/campaign.py status <campaign>
python3 <skill>/scripts/campaign.py next-action <campaign>
```

Any invalid receipt blocks completion. When `status` reports an obsolete
discovery receipt whose output is absent and a current receipt for the same
result exists, run:

```text
python3 <skill>/scripts/campaign.py repair-receipts <campaign>
```

The repair is deliberately narrow and retains every ambiguous receipt.

Follow its action: `discover`, `synthesize`, `dispatch`, `wait`, `integrate`,
`repair`, `finalize`, or `report_blocked`. `may_finish: false` forbids a normal
completion answer. Pause only when `may_pause: true`; for
`terminal: platform_blocked`, report the temporary platform boundary without
claiming campaign completion.

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
`scope_mapped_with_deferred_leads` means useful results were published after
the single pass while named coverage gaps remain.
