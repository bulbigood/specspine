# Parallel brownfield mapping

Use parallel mapping to shorten discovery for a large repository with several
independent architectural areas. Preserve iterative breadth-before-depth
mapping: parallelism changes execution, not the standard for creating a useful
specification.

## Preconditions

- Resolve and read the live `<spine-root>`.
- Perform or confirm a breadth-first survey before deep parallel work.
- Use a source revision that remains stable for the entire mapping run.
- Use ordinary sequential mapping when subagents are unavailable or the
  remaining questions overlap too heavily for independent investigation.

Do not use a requested or desired document count to plan areas, worker prompts,
splits, or stopping decisions.

## Initialize the run

Inspect the repository shape and current Mapping status. Build an initial
backlog of architectural questions, not directory assignments. Track every
question as ready, active, or blocked by named prerequisites. Each question
should have:

- a durable responsibility, runtime boundary, cross-cutting flow, or ownership
  problem to investigate;
- a disjoint primary evidence scope, while allowing workers to inspect
  integration edges;
- enough independence that another worker can proceed without its output;
- an explicit reminder to stop before reproducing implementation detail.

Do not assign two workers competing ownership of the same concept. Resolve
uncertain assignment overlap before spawning; there is no semantic integration
stage after workers finish.

After the breadth-first survey, choose a few broad final namespaces only when
the flat Spine is already difficult to navigate and stable cohesive clusters
are visible. Keep overview specifications at the root, use at most one
directory layer in normal cases, and never mirror the source tree. Plan
architectural questions first, then assign each question the applicable final
namespace as a publication destination. Reuse this layout throughout the run;
do not reorganize the live Spine while mapping remains active.

Use the largest safe concurrency:

```text
min(available worker slots, independent questions, safe repository I/O)
```

The orchestrator is the only agent allowed to spawn mapping workers. Workers
must not spawn further workers.

## Schedule as producer-consumer

Maintain one continuous dependency-aware ready queue, active worker set, and
blocked-question set. Keep the backlog bounded to material architectural
questions, not a requested document count. Start the largest safe active set.
When the environment can report individual worker completion and launch
replacements, use a rolling producer-consumer loop:

1. Consume each worker result as soon as that worker finishes.
2. Mechanically publish its files without waiting for other active workers.
3. Update question dependencies and add material follow-up questions from the
   worker report without stopping active workers.
4. Immediately launch the next ready question into the freed slot.
5. Wait again only after publication, queue maintenance, and slot refill have
   been handled.

Do not wait for all active workers to finish while a ready question and a safe
worker slot are available. Keep active concurrency at the largest safe level
until no question is ready. Publication and slot refill may be ordered
according to the environment's scheduling mechanics, but do not leave the slot
intentionally idle while reviewing or integrating a completed result.

If the environment exposes only barrier-style batch completion or cannot refill
slots safely, use its barrier primitive as a transport limitation and report
that limitation; do not introduce conceptual waves or delay already-ready work
beyond what the environment requires. Move a blocked question to ready as soon
as its prerequisites are satisfied. Keep questions that require unfinished
results, authority, or boundary resolution blocked rather than speculating.

## Isolate worker writes

Create one disposable staging root per worker outside the live
`<spine-root>`. Give every worker:

- the repository root and immutable source revision;
- the live `<spine-root>` as read-only context;
- its private staging root as the only writable documentation location;
- the relative destination under `<spine-root>` represented by that staging
  root;
- the final namespace assigned to its architectural question;
- one architectural question;
- the Map skill and applicable project instructions.

Workers may read existing specifications to avoid duplicate ownership, but
must not modify the repository, the live Spine, another worker's staging root,
or `README.md`. They create only publish-ready specification nodes in their
private staging root. Do not create assessments, reviews, integration notes, or
other artifacts that are not intended to become live specifications.

Each worker owns the complete quality of its files. Before finishing, it must:

- inspect every source it cites;
- avoid ownership already covered by the live Spine;
- choose final paths that do not collide with the live Spine;
- write links relative to the files' final locations under `<spine-root>`;
- satisfy the Map semantics and format rules;
- leave every file ready to publish without content changes.

Do not preallocate a number of documents. A worker may create no document when
the live Spine already answers the question or further detail would reproduce
code. If a publish-ready path already exists inside its staging root, choose
another meaningful concept name and report the final path; never overwrite it
or add an arbitrary numeric suffix.

Require each worker to report:

- evidence inspected;
- publish-ready files created and their relative destination paths;
- mapped responsibilities and relationships;
- material follow-up architectural questions and their prerequisites;
- unconfirmed inferences and open questions;
- whether no useful new node was found.

## Consume and publish results

As soon as each worker finishes, mechanically move every publish-ready file
from its private staging root to the same relative path under `<spine-root>`.
Do not wait for the rest of the active workers. Do not read or review file
contents, inspect repository source, repeat evidence validation, compare
ownership, merge or reject documents, rewrite content or links, update existing
specifications, update `README.md`, run SpecSpine Doctor, or run a whole-Spine
audit. Worker output is the published output.

Before moving, compare destination path names only. Never overwrite an existing
live file or another worker's destination. Return a colliding file to its worker
to choose a different meaningful path, then publish it unchanged. This is a
mechanical collision check, not semantic integration.

Raw parallel publication is intentionally exempt from the ordinary requirement
to make every new node reachable from the architecture index during the same
operation. Defer navigation cleanup until the single post-saturation
normalization.

Remove each empty staging root immediately after its files are moved. Never
leave staged copies as a second architecture source.

## Continue to saturation

Perform planning incrementally from completion reports without pausing active
workers. Reach saturation only when:

- the ready queue is empty;
- no mapping worker is active;
- every blocked question is either resolved, moved to ready, or explicitly
  deferred because it requires authority or unavailable evidence; and
- completion reports reveal no material independent architectural gap worth
  another worker.

When an external process uses repeated no-change runs as a saturation signal,
distribute those probes across distinct areas and cross-cutting flows; repeated
probes of one mature area do not establish whole-repository saturation.

Do not invoke SpecSpine Doctor during the mapping run, including between worker
completions. Do not normalize or reorganize the live Spine while any mapping
worker is active or any question remains ready or resolvably blocked.

## Normalize once after saturation

After saturation, perform one sequential normalization using only files under
`<spine-root>`; do not inspect repository source. Read the complete live
SpecSpine and:

1. Keep the established namespace layout when it remains adequate.
2. If the flat namespace is difficult to navigate and stable cohesive clusters
   are now visible, move specifications into a few broad lowercase kebab-case
   directories, normally with at most one directory layer. Never mirror the
   source tree.
3. Update affected relative links and curated `README.md` navigation so every
   specification is reachable.
4. Preserve architectural prose, accepted intent, evidence baselines, semantic
   IDs, unconfirmed inferences, and open questions. Do not merge, reject,
   reinterpret, or otherwise semantically rewrite worker output.
5. Verify affected links and semantic-ID references, then run the deterministic
   SpecSpine checker when it is available.

This normalization is part of completing a parallel Map request and needs no
separate prompt. Perform it once, not during continuous mapping.

## Optional post-map Doctor

Invoke SpecSpine Doctor only when the current request explicitly includes a
post-map semantic review. Run it once after saturation, normalization, and
mechanical checking. Doctor must inspect only `<spine-root>`, must not inspect
repository source, and must propose an exact repair batch before writing.
Apply semantic repairs only after operator approval.

Use a Doctor request equivalent to:

```text
Review the complete mapped and normalized SpecSpine at <spine-root> without
inspecting repository source. Inspect every specification for duplicate
ownership, unnecessary fragmentation, stale overview text, hidden direct
relationships, and excessive implementation detail. Propose an exact repair
batch, identify decisions that require authority, and ask the operator to
approve the batch before writing.
```
