# SpecSpine Map exhaustive orchestration

## Scope and authority

Map exactly the scope requested by the operator: one focused concern, several
areas, or the whole repository. Treat the scope the same way as SpecSpine Map;
exhaustive mode changes execution strategy, not mapping semantics.

Repository evidence may establish observations and support inferences, but
never establishes accepted decisions or constraints. Do not modify production
code, claim complete code/spec conformance, or perform semantic repair.
SpecSpine Doctor is outside this run: never invoke it during exhaustive Map.

Resolve the repository root and `<spine-root>`. Read the Spine index and
relevant specifications, then discover evidence adaptively for the requested
scope. Resolve one current evidence baseline once and include its exact marker
in shared producer context. Do not prescribe a universal listing command,
fixed traversal depth, document count, or initial backlog size.

For a focused request, follow the connected architectural boundary as far as
repository evidence remains relevant. For a whole-repository request, identify
the system shape and material top-level branches, then deepen each branch.
Prefer stable responsibilities, boundaries, interfaces, runtime and data
flows, persistence, integrations, configuration, deployment, security,
failure behavior, and observability over directory or implementation detail.
Repository listings, registries, manifests, route tables, and composition roots
may be enumerated internally to discover the coverage frontier. The prohibition
on mirroring source structure applies to published specifications, not to
discovery or scheduling.

For whole-repository work, account for eligible production paths or cohesive
path groups using `mapping-method.md`. Exclude tests and generated code from
compression estimates, not evidence discovery. Keep the inventory out of
published Markdown. Use `1:10` only as an advisory signal; qualitative value
decides depth.

## Own the durable branch frontier

The orchestrator is the sole scheduling authority. Create a unique temporary
run root outside the live Spine with `mktemp -d`. Use
`<run-root>/frontier.json` as the sole durable branch-scheduling record and
mutate it only through `python3 <map-skill-root>/scripts/frontier.py`. Producer
staging is disposable: only published Spine files and ledgered branch state
survive interruption. The helper writes atomically. Never put this control
state in the repository or producer staging.
Initialize it before discovery:

```text
python3 <map-skill-root>/scripts/frontier.py init \
  <run-root>/frontier.json --scope <operator-scope> \
  --root-question <root-question>
```

The ledger records stable lowercase kebab-case branch IDs, parent, question,
state, owner, prerequisite, intended namespace, terminal reason, and
resolution, plus exact published and replacement-reserved paths. States are
`queued`, `active`, `locally_saturated`, `blocked`, and
`complete`. Treat it as a write-ahead frontier: add every observed branch
before continuing past the evidence or checkpoint that exposed it. Commands
are idempotent when their complete branch data agrees and reject conflicting
reuse of an ID.

Use `add <ledger> <id> --parent <id> --question <text> --origin <evidence>`
for a new branch, adding `--prerequisite` and `--namespace` when known. Use
`documented` with the same identity fields plus `--document <relative-path>`
only after verifying its canonical owner. Before dispatch or publication use
`reserve --path <relative-path>` for every exact destination, adding
`--replace-existing <same-path>` only for an approved replacement. Reservations
are globally exclusive; use `unreserve` before selecting another unpublished
destination. Use `assign --owner <handle>` after a producer handle exists,
`release` after a failed start or resolved blocker,
`state ... blocked --terminal-reason <reason>`, and `state ...
locally_saturated --terminal-reason <exact-refusal>`. Use `state ... complete`
bottom-up and `ready` to select dispatchable work. Run the command with `--help`
if exact argument placement is unclear. Pass `--compact` to every mutating
frontier command so routine receipts do not inject the complete ledger into
agent context. Use `summary` when scheduling needs a compact state view.

Treat producer capacity as observed, not planned; an exact limit need not be
known in advance. Keep a branch `queued` and unowned until the environment
confirms a usable, addressable producer handle. Only then assign that handle,
mark the branch `active`, and count its slot. A failed start or missing handle
leaves the branch queued and does not reserve capacity; durable destination
reservations remain attached to the queued branch. Capacity exhaustion
reduces concurrency: it never completes, drops, or blocks queued work and does
not imply that every subagent is unavailable. Continue with confirmed sessions
and retry ready branches only after capacity may have been released. When the environment exposes subagents, attempt to start producer subagents and use every safely available slot; never choose local execution for convenience or unknown capacity, only after no usable producer handle can be obtained.

If a confirmed producer fails before returning a valid checkpoint, keep its
staging unpublished, clear its ownership, and requeue the branch with fresh
private staging unless an authority or prerequisite blocker was reported.
Never count planned, attempted, failed, or terminated sessions as active.
Never interrupt a running producer to switch to local execution, reclaim a
slot, or because it has not responded yet. Interrupt only for operator
cancellation or a confirmed hang or failure.

If all actual start attempts return no addressable handle, reserve the local
branch destinations, run `assign <ledger> <branch-id> --owner local`, and
execute the same branch protocol locally. On a later invocation every non-root
owner, including `local`, is stale: release it to `queued`, then assign a new
producer handle or `local` before continuing.

Split the initial scope into independent coherent architectural branches.
Avoid competing ownership of the same concept. Assign one branch to one
producer session and never repurpose that session for an unrelated branch.
Give each initial assignment exactly one independent architectural branch
question. Never combine sibling responsibilities to reduce producer starts or
fit available slots; leave undispatched siblings queued.
The producer may propose child branches but must never create producers.
Deduplicate proposals against the ledger and existing documents. The
orchestrator alone accepts forks, resolves prerequisites and namespace
ownership, and starts queued branches when slots are free. Record an already
documented boundary with the `documented` command and its exact owning
document; record every actionable fork with `add`. A failed start uses
`release`, never an implicit memory-only state change.

Seed and extend the ledger from the orchestrator's own inspected evidence
as well as producer proposals; producer proposals never define the completeness
of the requested scope. For every broad survey branch, maintain a coverage
frontier of directly observed independent responsibilities and classify its
eligible source groups. Reconcile each independent item to its own ledger
branch. A blocked item is a `blocked` child; an independently refused item must
be assigned, investigated, and transitioned through `locally_saturated` with
an evidence-based reason. Before the first producer starts on a
whole-repository request, seed material top-level branches from inspected
signals; add later signals as found.

A same-boundary continuation remains with its current producer. A materially
independent responsibility or boundary is a fork candidate for a new producer.
A terminal Map refusal closes only the exact branch question assigned to that
producer; it never closes the parent survey or sibling boundaries. A focused
branch becomes `locally_saturated` only after its owner reaches that exact
refusal and the orchestrator records the exact reason with `state`. A broad
survey branch cannot become `locally_saturated` until its owner
also reports every directly observed material child boundary and the
orchestrator imports each one into the ledger. A branch becomes `complete` only
when it is locally saturated and every child branch is complete; the helper
enforces this bottom-up transition.

## Prepare producer sessions

Use the initialized run root and create one private staging root per active
producer session. This state belongs only to the current invocation, but it is
the recovery point if execution is interrupted. Do not create control files
beside the repository or Spine. Published Spine files remain the durable
documentation result.

If the operator supplies a preserved ledger path from an interrupted run, do
not initialize a replacement. Audit that ledger without `--final`, reconcile
its published destinations with the live Spine, and run the full checker.
Treat every pre-existing private staging directory as untrusted and never
publish its candidates because the write-barrier report was not durably
consumed. Release stale `active` owners, rebuild reservations from ledgered
published/reserved paths and live destinations, create fresh staging, and rerun
those branches from their recorded questions. This resume-only reconciliation
may read published files when required; the ordinary no-reread optimization
does not survive process interruption. If a live destination is not ledgered,
do not infer its branch owner: rerun the recorded branch against the current
Spine or mark the collision `blocked`.
After releasing stale owners, immediately fill every safely available producer
slot from `ready`; do not start one branch and return a progress report while
other ready work or active producers remain.

Build the complete bounded Map producer bundle once at
`<run-root>/producer-instructions.md`:

```text
python3 <map-skill-root>/scripts/bundle_skill.py \
  <map-skill-root> <run-root>/producer-instructions.md --print
```

The builder includes `bounded-mode.md`, its required semantics, format and
mapping-method references, and every Markdown template. It explicitly excludes
the Map dispatcher and exhaustive orchestration so producers cannot recurse.
It saves the bundle and emits the same text. Capture stdout directly; do not
read the generated file or assemble resources manually. Embed the bundle only
in the initial command for each new producer session. Producers must not load
skills, resources, or orchestration instructions themselves.
Prefix every new `spawn_agent` message with the complete captured bundle,
including sibling starts and later refills; isolated producers share no bundle.
Do not redirect `--print` output to a second file, use shell command
substitution, or reread either output file to construct producer messages.

Start each producer with a medium-strength model in an isolated new-thread
context. With Codex `spawn_agent`, pass `agent_type="medium"` and
`fork_turns="none"`; elsewhere use the equivalent medium-capability role and
isolation. The initial command is self-contained; never copy the growing ToDo, sibling reports, or orchestration history.

Use this initial command with resolved placeholders:
```text
You are a SpecSpine mapping producer.

<complete-generated-map-instructions>

Producer execution override:

All Map instructions and resources needed for this branch are embedded above.
Do not load or invoke any skill, reference, template, or instruction file.
Never create another producer.

Own only the assigned architectural branch. Perform exactly one Map step in
this turn, then return a checkpoint immediately. Do not execute the reported
continuation in the same turn. Keep same-boundary continuations in this session.
Propose a fork only for a material independent responsibility or boundary that
another producer can own. Report every such boundary directly observed during
the current step, not only the most promising one. A refusal for one proposed
detail does not answer other children of a broader survey.

Create publish-ready Markdown only under the writable output root. Keep source,
tests, configuration, the live Spine, and every other staging root read-only.
Tool-level write access does not authorize live-Spine writes: every path you
create or replace in this turn must begin with the private staging root.
The writable root mirrors `<spine-root>`: place every candidate at its exact
final relative path. A candidate may be a new specification or a complete
replacement of a reserved live destination. Preserve unrelated content and
accepted intent in replacements. Never replace an unreserved path or README.
The reported destination must exactly equal the candidate path relative to the
staging root. The orchestrator rejects rather than relocates a misplaced
candidate because relocation changes Markdown link resolution.

Apply Map's refusal rules exactly. When they stop this branch, create nothing
and report `no useful node`; never manufacture output to keep the branch alive.
Any checkpoint that created or replaced a file must be `continuing`, never
`locally saturated`. A `locally saturated` checkpoint must be candidate-free
and follow a terminal Map refusal in that turn. Do not refuse while eligible
source lacks an owner, child branch, or concrete low-value classification.
Use the exact supplied evidence baseline near the first Observed section. Do
not perform a separate validation or reread pass; return the checkpoint.

Return a compact checkpoint report containing only:

- `Branch status`: `continuing`, `locally saturated`, or `blocked`;
- evidence inspected;
- created or replaced files and their final relative destinations;
- mapped responsibilities, boundaries, and relationships;
- related paths and navigation targets, marking replacement reservations;
- `Source coverage`: each inspected eligible production path group classified
  as mapped here, owned by a named specification, requiring a child branch, or
  lacking durable value with a reason; tests and generated code are
  evidence-only;
- `Current-branch continuation`: the next same-boundary work, or `none`;
- `Coverage frontier`: every directly observed material independent boundary
  outside the next same-boundary continuation, including children found inside
  a broad survey; for each give a suggested stable branch ID, exact question,
  evidence, prerequisite or `none`, suggested namespace, and classification as
  a fork candidate, already documented, or blocked; use `none` only when
  inspected evidence exposes no such boundary;
- `Fork candidates`: each independent branch question, reason, prerequisite,
  and suggested namespace, or `none`;
- unresolved inferences or drift;
- `no useful node` and its reason for terminal refusal.

Report work only when inspected evidence supports it. Do not repeat document
prose or speculate to extend the tree. Return the report as the agent result;
never write control files into staging.

Repository: <repository-root>
Live Spine, read-only: <spine-root>
Requested mapping scope: <operator-scope>
Shared repository and Spine context: <shared-context>
Evidence baseline marker for this run: <exact-evidence-baseline-marker>

Assignment:
Writable output root mirroring the Spine: <private-staging-root>
Final namespace: <relative-destination>
Reserved existing destinations: <relative-paths-or-none>
Architectural branch: <branch-question>
```

This protocol is entered only after the root capability gate observes a
subagent-creation mechanism. If actual start attempts all fail or return no
addressable handle, execute the same branch protocol locally; the current agent
performs orchestrator, producer, and consumer roles, and only concurrency
changes. Never infer runtime failure without an attempted start.

## Consume checkpoints and resume

Treat a returned checkpoint as a write barrier: the producer must not mutate
its staging root until the orchestrator has consumed it. Do not reread
candidate prose or repeat source investigation. If staging is nonempty, publish
it only through this single consumer command:

```text
python3 <map-skill-root>/scripts/publish_candidates.py \
  <run-root>/frontier.json <branch-id> <spine-root> <private-staging-root> \
  --path <candidate-relative-path>... \
  [--replace-existing <reserved-relative-path>]...
```

Omit `--replace-existing` entirely when the producer reserved no existing
destination; never pass the brackets, ellipsis, or the word `none`.
The helper is the sole producer-publication route. It requires an active owner,
exact agreement between declared destinations and staging-relative paths,
durable conflict-free reservations, and a clean candidate check. The live
check temporarily defers only reachability and translated-ID notes until
normalization. Any nonzero exit, `error` object, malformed output, or other
finding blocks
classification and leaves live files untouched. The helper moves accepted
candidates unchanged, rolls file moves back on a later failure, then records
publication and emits one compact receipt. Never reproduce these stages in a
shell pipeline, manually move or rewrite a candidate, bypass the helper, or
continue after a failed receipt. Resolve findings through the same producer
session. If interruption nevertheless leaves an unledgered live destination,
rerun that branch against the current Spine and never infer ownership from the
file.

Classify the report after publication. Import its complete `Coverage frontier`
into the ledger before resuming or releasing that producer:

- accept conflict-free reservation requests and keep published paths reserved;
- reject terminal status while its `Source coverage` contains an unowned group;
- reconcile every `Coverage frontier` item against the ledger and existing
  documented branches; add every actionable unowned boundary;
- add accepted `Fork candidates` as child branches;
- retain blocked work with its prerequisite or authority requirement;
- mark the branch `locally_saturated` only after terminal `no useful node`.

Treat any checkpoint that published a candidate as `continuing`, regardless of
its reported status or missing continuation. Resume that same producer with a
terminal-depth assignment; only a later candidate-free `no useful node`
checkpoint may release the session as locally saturated. The refusal must use
`no useful node: <evidence-based reason>`; a bare phrase is invalid.

Reject a broad survey's `locally saturated` status when its mapped
responsibilities or relationships expose material independent boundaries that
are absent from its coverage frontier. Ask the same producer for the missing
frontier classification; do not ask it to map those sibling branches. Treat
`no useful node` as scoped to the exact assigned question and stated refusal
reason, never as proof that its parent or siblings lack useful nodes.

Resume a continuing branch through the environment's native follow-up
mechanism. Send only the next same-branch assignment and relevant paths
published since its previous turn; never resend the bundle or immutable shared
context. Resume only after staging is empty. Do not assign unrelated queued
work to that session. Once a branch is locally saturated, release its session
and fill the slot from the ledger's `ready` output.

Use this compact continuation command:

```text
Continue the same architectural branch; do not reload or repeat immutable
instructions. Perform exactly one Map step for this same-boundary continuation:
<continuation-or-terminal-depth>.
Reserved branch destinations, including newly published paths: <paths-or-none>.
The writable staging root is empty and remains <private-staging-root>.
Return the same compact checkpoint report.
```

Defer index reachability and reciprocal navigation updates until final
normalization so producers never compete over shared overview files.

## Reach saturation

Keep ready slots occupied with queued independent branches while preserving
branch ownership and prerequisites. Do not use batch barriers. Continue each
owner session one Map step per checkpoint until it reports terminal `no useful
node`; do not create a fresh producer merely to probe the same branch.
Immediately dispatch ready work into every free slot. Continuing owners and
queued branches are both ready work: dispatch them without waiting for siblings
or forming pairs or waves. When several results arrive, classify only enough to
keep dispatching until all available slots are occupied.
After consuming any candidate-free terminal checkpoint, spawn one ready queued
branch before calling `wait`, listing agents, or processing another sibling
result. Never wait for another active owner while that free slot has ready work.
The run is saturated only when no producer is active, no actionable branch
remains, and every requested branch tree is complete. Do not stop at a
predetermined document count or shallow overview coverage, and do not invent
branches solely to prove depth. Before closing a branch, apply the qualitative
coverage, information-gain, change-utility, and visual criteria. The advisory
`1:10` ratio can trigger review but never force prose.
Whenever the ready queue first becomes empty, repeat scope-level discovery
against the current repository evidence. For a whole repository, revisit every
material architecture-signal class that exists there: composition roots,
registries and manifests, routes and public interfaces, persistence, external
integrations, configuration and deployment, security boundaries, failure
behavior, and observability. Add any newly exposed independent boundary and
drain the queue again. The root branch may become `locally_saturated` only when
one complete repeat pass adds no unledgered material boundary.
After every terminal result, close complete descendants bottom-up with `state`.
Before normalization, run:

```text
python3 <map-skill-root>/scripts/frontier.py audit \
  <run-root>/frontier.json --final
```

Proceed only when it exits zero and prints `[]`. Any `queued`, `active`,
`blocked`, or `locally_saturated` entry is remaining work, not a limitation to
mention after stopping. Also audit the ledger against coverage frontiers and
discovery evidence already inspected. A broad overview that names independently
evolving responsibilities without child ledger entries is remaining actionable
work, even when every current producer has returned `no useful node`.

Treat exhaustive work as a resumable campaign, not a promise that a large
repository fits one invocation. Do not stop for elapsed time, fatigue, a
document milestone, or progress while the environment permits. A normal final
requires a clean final audit or only concrete blocked branches with exact
unblock input. If the operator or host interrupts the invocation, preserve the
ledger and report an incomplete campaign checkpoint without claiming
saturation.

Do not reorganize the live Spine or perform final normalization while mapping
branches remain.

A branch is `blocked` only when a concrete missing permission, unavailable
evidence, unresolved destination conflict, or operator decision prevents safe
progress. Retry recoverable execution failures while another safe approach
exists. When only blocked work remains, stop without claiming saturation,
preserve the run root, report each branch and exact unblock condition, and ask
for that input. On a later invocation, verify the condition, release the branch
to `queued`, and continue.

## Normalize once

After saturation, perform one sequential navigation pass using producer
reports, published destinations, the Spine index, and relevant overviews:

Do not reread published producer documents; use their reports and destinations.
Reading pre-existing indexes and overviews and running the checker remain allowed.

1. Keep the established layout unless cohesive clusters make navigation
   materially difficult. Never mirror the source tree.
2. Add every new document to curated `README.md` navigation.
3. Apply evidence-supported reciprocal links to named overview documents and
   update affected relative links.
4. Preserve producer prose, claim semantics, semantic IDs, unresolved
   inferences, and open questions.
5. Run the full deterministic checker once over the normalized Spine.

After success, remove the exact disposable run root with `find <run-root> -depth
-delete`; never try `rm -rf`. If interrupted or blocked before a clean final
audit, do not normalize or delete the run root: report the exact ledger and
staging paths so a later invocation can continue them. Report scope, published
files, relationships, exact `no useful node` reasons, unresolved drift,
limitations, normalization, and checks.
The final report must contain the literal phrase `no useful node` and recommend
that the operator run `$specspine-doctor` in a new session for an independent
integrity and semantic review. Do not invoke Doctor in the current session.
