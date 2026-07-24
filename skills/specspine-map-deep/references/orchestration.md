# SpecSpine Map Deep orchestration

## Scope and authority

Map exactly the scope requested by the operator: one focused concern, several
areas, or the whole repository. Treat the scope the same way as SpecSpine Map;
Map-Deep changes execution strategy, not mapping semantics.

Repository evidence may establish observations and support inferences, but
never establishes accepted decisions or constraints. Do not modify production
code, claim complete code/spec conformance, or apply semantic Doctor repairs
without approval.

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

## Own the branch ToDo

The orchestrator is the sole scheduling authority. Keep an in-memory tree of
branches with their parent, question, state, owner session, prerequisites,
intended namespace, reserved live destinations, and accepted children. States
are `queued`, `active`, `locally saturated`, `blocked`, and `complete`. Do not
write this control state into the repository or staging.

Split the initial scope into independent coherent architectural branches.
Avoid competing ownership of the same concept. Assign one branch to one
producer session and never repurpose that session for an unrelated branch.
The producer may propose child branches but must never create producers.
Deduplicate proposals against queued, active, locally saturated, complete, and
already documented branches. The orchestrator alone accepts forks, resolves
prerequisites and namespace ownership, and starts queued branches when slots
are free.

A same-boundary continuation remains with its current producer. A materially
independent responsibility or boundary is a fork candidate for a new producer.
A branch becomes `locally saturated` only after its owner reaches a terminal
Map refusal. It becomes `complete` only when it is locally saturated and every
accepted child branch is complete.

## Prepare producer sessions

Create a unique disposable run root outside the live `<spine-root>` and one
private staging root per active producer session. This state belongs only to
the current invocation. Do not create a ledger, checkpoint, recovery manifest,
source inventory, or resumable run protocol. Published Spine files are the
durable result. If interrupted, report remaining staging paths; a later run
rediscovers coverage from the current Spine.

Build the complete Map instruction bundle once at
`<run-root>/producer-instructions.md`:

```text
python3 <map-deep-skill-root>/scripts/bundle_skill.py \
  <map-skill-root> <run-root>/producer-instructions.md --print
```

The builder includes the Map body, every UTF-8 file under Map `references/`,
and every UTF-8 Markdown file under Map `assets/templates/`. It saves the
bundle and emits the same text. Capture stdout directly; do not read the
generated file or assemble resources manually. Embed the bundle only in the
initial command for each new producer session. Producers must not load skills,
resources, or orchestration instructions themselves.

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
another producer can own.

Create publish-ready Markdown only under the writable output root. Keep source,
tests, configuration, the live Spine, and every other staging root read-only.
The writable root mirrors `<spine-root>`: place every candidate at its exact
final relative path. A candidate may be a new specification or a complete
replacement of a reserved live destination. Preserve unrelated content and
accepted intent in replacements. Never replace an unreserved path or README.

Apply Map's refusal rules exactly. When they stop this branch, create nothing
and report `no useful node`; never manufacture output to keep the branch alive.
Use the exact supplied evidence baseline near the first Observed section. Do
not perform a separate validation or reread pass; return the checkpoint.

Return a compact checkpoint report containing only:

- `Branch status`: `continuing`, `locally saturated`, or `blocked`;
- evidence inspected;
- created or replaced files and their final relative destinations;
- mapped responsibilities, boundaries, and relationships;
- related paths and navigation targets, marking replacement reservations;
- `Current-branch continuation`: the next same-boundary work, or `none`;
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

When subagents are unavailable, execute the same branch protocol locally. The
current agent performs orchestrator, producer, and consumer roles; only
concurrency changes.

## Consume checkpoints and resume

Treat a returned checkpoint as a write barrier: the producer must not mutate
its staging root until the orchestrator has consumed it. Do not reread
candidate prose or repeat source investigation. If staging is nonempty, run:

```text
python3 <checker-path>/check_spine.py <spine-root> \
  --candidates <private-staging-root> <reserved --replace-existing args or none> --json
```

Resolve findings through the same producer session. A nonzero exit or nonempty
JSON, including a note, blocks publication; never bypass it. Move every accepted
candidate unchanged after zero findings. Replace only a destination reserved
for that producer. Never reconstruct a file by reading and rewriting it, reread,
replace an unreserved path, or add an arbitrary numeric suffix.

Classify the report after publication:

- accept conflict-free reservation requests and keep published paths reserved;
- enqueue accepted `Fork candidates` as child branches;
- retain blocked work with its prerequisite or authority requirement;
- mark the branch locally saturated only after terminal `no useful node`.

Resume a continuing branch through the environment's native follow-up
mechanism. Send only the next same-branch assignment and relevant paths
published since its previous turn; never resend the bundle or immutable shared
context. Resume only after staging is empty. Do not assign unrelated queued
work to that session. Once a branch is locally saturated, release its session
and fill the slot from the branch ToDo.

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
The run is saturated only when no producer is active, no actionable branch
remains, and every requested branch tree is complete. Do not stop at a
predetermined document count or shallow overview coverage, and do not invent
branches solely to prove depth.

Do not invoke SpecSpine Doctor, reorganize the live Spine, or perform final
normalization while mapping branches remain.

## Normalize once

After saturation, perform one sequential navigation pass using producer
reports, published destinations, the Spine index, and relevant overviews:

1. Keep the established layout unless cohesive clusters make navigation
   materially difficult. Never mirror the source tree.
2. Add every new document to curated `README.md` navigation.
3. Apply evidence-supported reciprocal links to named overview documents and
   update affected relative links.
4. Preserve producer prose, claim semantics, semantic IDs, unresolved
   inferences, and open questions.
5. Run the full deterministic checker once over the normalized Spine.

After success, remove the exact disposable run root with `find <run-root> -depth
-delete`; never try `rm -rf`. Report scope, published files, relationships, exact
`no useful node` reasons, unresolved drift, limitations, normalization, and checks.

Run SpecSpine Doctor only when the operator explicitly requests a post-map
semantic review; apply repairs after final checks and only with approval.
