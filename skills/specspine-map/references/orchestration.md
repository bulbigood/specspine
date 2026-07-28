# SpecSpine Map exhaustive orchestration

An exhaustive campaign closes one operator-defined semantic scope. The scope
may be Kafka, a subsystem and its related services, or the whole repository.
Whole-repository mapping is the same campaign with a broad scope and an
optional flat-file discovery accelerator.

## Invariants

- Only root runs `campaign.py`.
- Discovery scouts expand one semantic lead by one level. Fresh curators merge
  child proposals between levels. One final synthesis agent creates the producer
  frontier. One fresh producer handles each uncovered topic.
- Use the medium-capability general-purpose tier for every agent:
  `agent_type: medium` in Codex. Use a fresh isolated context
  (`fork_turns: none`) and only the phase contract and inputs.
- Never fall back to a weak or strongest tier. Preserve the work and report a
  concrete blocker when fresh medium-tier agents are unavailable.
- Discovery hierarchy and inventory pagination are provenance, never
  architecture.
- A flat production-file inventory is only a repository-scope accelerator. It
  grants no owner, topic, coverage, or completion authority.
- Producers write only to private staging. Root integrates centrally.
- Dispatch strict waves of at most five; never refill a running wave.
- A safety depth, agent, time, or topic limit may block a campaign but never
  establish scope closure.

## Start

Create a durable private run root outside the repository. Follow
`campaign-selection.md`; never silently select a campaign by directory order.

```text
python3 <map-skill-root>/scripts/campaign.py init \
  <run-root>/campaign.json \
  --scope <requested-scope> \
  --root-question <scope-question> \
  --repository-root <repository-root> \
  --spine-state <empty-or-existing>
```

For an existing Spine, run the mechanical index from
`documentation-first-seeding.md`.

Write `<run-root>/scope.json`:

```json
{
  "kind": "topic",
  "title": "Kafka and related services",
  "question": "Which components publish, consume, configure, deploy, observe, recover, or own contracts for Kafka traffic?",
  "inclusion_rule": "Include direct Kafka runtime, contract, operational, failure, deployment, producer, and consumer responsibilities.",
  "exclusion_rule": "Exclude components connected only through shared infrastructure or unrelated domain calls."
}
```

Use `kind: repository` only when the requested topic is the whole repository.
Do not broaden a topic merely to make discovery easier.

## Close the discovery frontier

Start discovery:

```text
python3 <map-skill-root>/scripts/campaign.py discovery-start \
  <repository-root> <spine-root> <run-root>/scope.json \
  <run-root>/discovery
```

For repository scope, normally add `--inventory-accelerator`. It supplies every
mechanically recognized text production file as neutral seed pagination. Do
not use it for a bounded topic: semantic scouts must find the relevant files.

Run the `scope-root` scout first so broad discovery starts from
`<spine-root>/README.md` and the operator's semantic question. For repository
scope, treat the neutral inventory packets and root child leads as the next
level.

Launch one fresh scout per packet. Execute a discovery level in strict
subwaves of at most five without starting its children. Give each scout:

```text
Read <map-skill-root>/references/discovery-task.md completely; it is your sole
Map contract. Analyze <discovery-packet> against <repository-root> and
<spine-root>. Write the result to <matching-discovery-result>. Do not read
other Map references or message other agents. Terminate after writing it.
```

After every packet at the current level settles, launch one fresh curator with:

```text
Read <map-skill-root>/references/frontier-curation.md completely; it is your
sole Map contract. Read <scope.json>, the settled level results, and the compact
registry of prior packet leads and frontier decisions. Write
<next-frontier.json>. Do not inspect source, read other Map references, or
message other agents. Terminate after writing it.
```

Create the next level:

```text
python3 <map-skill-root>/scripts/campaign.py discovery-packets \
  <run-root>/discovery/discovery-seed.json \
  <next-frontier.json> <run-root>/discovery/wave-NNNN
```

Repeat level expansion then curation until the curator emits no queued decisions and
every proposal is `duplicate` or `out_of_scope`. Never dispatch an additional
file planner for evidence a semantic scout already classified. Neutral file
packets are needed only for the repository accelerator or for a mechanically
added bulk/orphan set that no scout classified.

Collect and mechanically validate the closed graph:

```text
python3 <map-skill-root>/scripts/campaign.py discovery-collect \
  <run-root>/discovery/discovery-seed.json \
  <run-root>/discovery <run-root>/discovery-results \
  <run-root>/discovery-corpus.json
```

The collector rejects missing scout results, unclassified seed files,
undispositioned child proposals, unknown duplicates, stale source files,
invalid scope paths, and queued leads without results.

## Synthesize the producer frontier

Launch exactly one fresh synthesis agent:

```text
Read <map-skill-root>/references/topic-synthesis.md completely; it is your sole
Map contract. Synthesize <discovery-corpus.json> against <repository-root> and
check every semantic topic against <spine-root>. Write
<run-root>/topic-plan.json. Do not read other Map references or message other
agents. Terminate after writing it.
```

If `open_leads` is nonempty, do not create producers. Reopen discovery:

```text
python3 <map-skill-root>/scripts/campaign.py discovery-reopen \
  <run-root>/discovery/discovery-seed.json \
  <run-root>/topic-plan.json <run-root>/discovery/wave-NNNN
```

Run scouts and frontier curation again, rebuild the corpus at a new path, and
rerun whole-corpus synthesis. Continue until `open_leads` is empty.

Record the immutable scope pass:

```text
python3 <map-skill-root>/scripts/campaign.py source-pass \
  <campaign> <repository-root> <spine-root> \
  --discovery-corpus <run-root>/discovery-corpus-final.json \
  --topic-plan <run-root>/topic-plan-final.json
```

The command validates the current scope snapshot, complete evidence
disposition, existing-Spine coverage documents and semantic claims, and then
creates one immutable producer ToDo per uncovered semantic topic. `covered`
and `supporting` remain auditable without producers. Candidate owners never
close work.

## Dispatch producer waves

At a wave boundary:

```text
python3 <map-skill-root>/scripts/campaign.py ready <campaign> --limit <wave-size>
```

For each selected task, prepare a packet and unique sibling work/handoff paths:

```text
python3 <map-skill-root>/scripts/campaign.py packet \
  <campaign> <task-id> --output <run-root>/packets/<task-id>-<attempt>.json
```

Give each fresh producer only:

```text
Handle exactly one exhaustive SpecSpine Map ToDo.
Contract: read <map-skill-root>/references/producer-task.md completely; it is
your sole Map contract. Do not read SKILL.md or any other Map reference.
Task: <task-packet.json>; roots: repository=<repository-root>; Spine=<spine-root>
Packages: work=<work-package>; handoff=<handoff-package>
Finalize script: <map-skill-root>/scripts/producer_finalize.py
Do not message other agents. Terminate after the atomic handoff.
```

Precompute the entire wave and emit spawn calls back-to-back. After every
handle returns, assign the whole wave:

```text
python3 <map-skill-root>/scripts/campaign.py assign \
  <campaign> <task-id> --owner <fresh-agent-path>
```

Wait for the terminal barrier without refill. Harvest all available immutable
handoffs:

```text
python3 <map-skill-root>/scripts/campaign.py harvest-wave \
  <campaign> <run-root>/handoffs <spine-root> <run-root>/harvest
```

After every wave member is completed, failed, or cancelled, accept or release
the whole wave:

```text
python3 <map-skill-root>/scripts/campaign.py accept-wave \
  <campaign> <run-root>/handoffs <spine-root> <run-root>/harvest
```

Never inspect or accept `producer-work`; only atomically renamed handoffs are
eligible. Root reruns every acceptance check. Preserve valid siblings when one
handoff fails. Release failed attempts only after the barrier. Never reuse a
producer. If fresh medium-tier agents are unavailable, block actionable tasks
instead of substituting another tier.

## Integrate and derive ToDo

After every settled wave, follow `integration-pass.md`: prepare one private
workspace, disposition every result, anchor, and suggestion, then publish the
checked workspace and ledger update atomically. Never edit live Spine between
acceptance and integration. Repeat cumulative document history in every
progress or final report.

Repeat:

```text
ToDo → producer wave → barrier → acceptance → one integration → derived ToDo
```

An empty ready list does not skip integration: tasks may remain in `review` or
`published`. `published` means a private accepted draft, not a live document.

## Continuity and completion

The durable campaign is the unit of completion. Before `source-pass`, an
unavoidable turn boundary is clean only between discovery levels: every
launched scout and curator has terminated, every packet/result/decision is
durable, and no partially dispatched level exists. Report the exact run root,
completed levels, and next frontier; this is a pause, never completion.

After `source-pass`, at campaign start, after every integration, after resume,
and before any final answer run:

```text
python3 <map-skill-root>/scripts/campaign.py next-action <campaign>
```

Follow `action`:

- `dispatch` — start one bounded producer wave;
- `wait` — wait for the assigned wave;
- `integrate` — integrate settled results;
- `repair` — restore current source, Spine, integration, or checker state;
- `finalize` — run `finalize_run.py`;
- `report_blocked` — report the concrete preserved blocker.

`may_finish: false` forbids a final answer. An unavoidable platform boundary
allows a resumable progress final only when `may_pause: true`; name the exact
ledger and remaining counts. Never stop with assigned, review, or private
publication work.

`scope_verified` requires:

- the discovery graph was closed and synthesized with no `open_leads`;
- every producer topic is complete;
- no `todo`, `assigned`, `review`, `published`, or `blocked` task remains;
- every result and suggestion was integrated;
- the recorded scope snapshot and live Spine hashes are current;
- the v3 checker is clean and the latest integration created no ToDo.

For repository scope this verifies the broad scope seeded by the flat inventory.
For topic scope it verifies the declared semantic frontier. Neither status
claims that no conceivable architectural concept exists.

After `scope_verified`, make no further edits. Run `finalize_run.py`, report the
scope, discovery and verification counts, publications, and uncertainty, and
recommend `$specspine-doctor` in a separate session.
