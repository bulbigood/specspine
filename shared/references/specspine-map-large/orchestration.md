# Large-repository mapping orchestration

## Preconditions

- Resolve and read the live `<spine-root>`.
- Perform or confirm a shallow breadth-first topology survey.
- Capture a concise source revision and dirty-state fingerprint when available.
  Exclude `<spine-root>` and the disposable run root from the fingerprint.
  Verify that identifier before publishing results and at completion. If it
  changes, stop rather than mix evidence from different source states.

If the Spine does not yet have `README.md`, create a minimal index and
topology-level entry points during the shallow survey before starting staged
production. Do not turn this bootstrap into deep repository mapping.

Do not use a requested or desired document count to plan areas, worker prompts,
splits, or stopping decisions.

## Initialize the run

Create one disposable run root outside the live `<spine-root>`. Keep private
staging roots and a small durable append-only ledger there. Record the source
identifier, question state changes, producer IDs, and published destination
paths. Append compact events without rereading or rewriting the ledger during
an uninterrupted run. Batch a checkpoint with the dispatch or publication
filesystem operation when the environment permits. On resume, read the ledger,
reconcile published paths, return interrupted active questions to ready, and
continue. Delete the run root after successful completion. If the run stops
incomplete, preserve and report its location for resumption.

Inspect only enough repository shape and current Mapping status to seed the run.
Do not deeply explore the codebase or enumerate every possible area up front.
Build only enough ready architectural questions to fill current producer
capacity plus a small reserve. Extend this bounded backlog from producer
reports. Assign exactly one coherent architectural zone to each producer. A
zone may contain related questions, but never combine independent zones merely
to amortize producer startup. Each assignment should have:

- a durable responsibility, runtime boundary, cross-cutting flow, or ownership
  problem to investigate;
- a disjoint primary evidence scope, while allowing workers to inspect
  integration edges;
- enough independence that another worker can proceed without its output;
- an explicit reminder to stop before reproducing implementation detail.

Do not assign two producers competing ownership of the same concept. Resolve
uncertain assignment overlap before dispatch; there is no source-aware semantic
integration stage after producers finish.

After the shallow survey, choose a few broad final namespaces only when
the flat Spine is already difficult to navigate and stable cohesive clusters
are visible. Keep overview specifications at the root, use at most one
directory layer in normal cases, and never mirror the source tree. Plan
architectural questions first, then assign each question the applicable final
namespace as a publication destination. Reuse this layout throughout the run;
do not reorganize the live Spine while mapping remains active.

When subagents are available, use the largest safe concurrency:
`min(actual worker slots, independent ready questions, safe repository I/O)`.

Reserve orchestrator capacity when the environment counts it in the total
concurrency limit. Assume available repository I/O is safe unless a documented
limit or observed contention requires less concurrency; report any reduction.
Set role/model in spawn metadata, never producer commands. Honor explicit
routing; otherwise use the cheapest reliable read-heavy role, not the stronger
orchestrator by inheritance. When a harness pins subagent defaults, use
`fork_turns=none` and do not override model or reasoning; the inline command is
self-contained. Otherwise select the cheapest reliable role in spawn metadata.
The orchestrator alone spawns mapping workers, and workers never spawn.

Treat every agent or thread ID returned by the environment as opaque. Copy the
exact ID from a successful spawn result into the ledger; never retype, derive,
or normalize it. Target wait, message, and close operations only with that
recorded ID. A `not_found` result is an orchestration transport error, never a
producer failure and never grounds for retry. Do not change the active set;
recover the exact returned ID from the spawn result or stop incomplete if it
cannot be recovered. Retry only after a recorded producer ID reaches an
explicit terminal `failed` state and its staging root has no publishable
result. Never start a duplicate producer while the original may still be
active.

## Schedule as producer-consumer

Maintain one continuous dependency-aware ready queue, active worker set, and
blocked-question set. Keep the backlog bounded to material architectural
questions. A completed producer report is the primary discovery mechanism: add
its material adjacent areas and cross-cutting questions to ready or blocked
without rereading repository source.

With subagents, start the largest safe active set. When the environment can
report individual worker completion and launch replacements, use a rolling
producer-consumer loop:

1. Record each completion report and its immutable staging root as soon as that
   worker finishes.
2. Before reading or publishing any candidate file, immediately launch the
   next already-ready question into the freed slot.
3. If no question is ready, inspect only enough of the completion report to
   update dependencies and enqueue material follow-up questions, then launch
   the next newly-ready question before candidate acceptance.
4. While the replacement producer runs, inspect and publish the completed
   producer's acceptable files, then finish queue maintenance from its report.
5. Wait again only after every safe slot has been refilled and all completed
   results have been consumed.

Use the environment's blocking completion notification or longest safe blocking
wait. Do not poll worker status, issue a preliminary empty or non-blocking wait,
or alternate status narration with wait calls. One completion should normally
cause one return to the orchestrator. If the environment itself returns early
without a completion, block again without replanning or restating queue state.

Do not wait for all active workers to finish while a ready question and a safe
worker slot are available. If the environment cannot refill before consuming a
completed result, report that transport limitation.

If only barrier completion is available, report that transport limitation; do
not introduce conceptual waves or delay already-ready work
beyond what the environment requires. Move a blocked question to ready as soon
as its prerequisites are satisfied. Keep questions that require unfinished
results, authority, or boundary resolution blocked rather than speculating.

When subagents are unavailable, use the same ledger, staging, publication,
backlog-growth, and saturation rules with the orchestrator as one local
producer. Take one bounded ready question, inspect only its relevant evidence,
write its candidates to staging, consume them, checkpoint, and immediately take
the next ready question. Never attempt to hold the whole repository map or all
source evidence in context at once. Report that execution was sequential
because subagents were unavailable.

## Isolate producer writes

Create one private staging root per active producer inside the disposable run
root. Build the shared topology snapshot, current ownership summary, source
revision, and applicable project instructions once in the orchestrator. Reuse
that text for every producer; do not make workers repeat common topology,
index, instruction, or revision discovery.

Pass every worker the complete command below as plain text with placeholders
resolved. Keep its shared prefix byte-identical and append producer-specific
assignment fields only at the end for prompt caching. Never add names or paths
of skills, references, templates, or instruction files.

```text
You are a SpecSpine mapping producer.

Do not load or invoke any skill, reference, template, or instruction file. Do
not spawn another agent. Use only this command and the project instructions
embedded below.

Inspect only evidence relevant to the assigned scope. Inspect every source
you cite. Repository evidence can establish Observed facts and support
Inferred interpretations; it cannot establish Decisions or Constraints.
Preserve conflicts with accepted intent. Model stable responsibilities,
boundaries, runtime or data flows, ownership, and relationships—not source-tree
shape or implementation procedure.

Create the smallest useful set of publish-ready Markdown specifications only
under the writable output root. Do not modify source, tests, configuration,
the live Spine, its README, or another staging root. Do not create a review,
plan, assessment, task list, implementation status, or Doctor report. It is
valid to create no file when the live Spine already answers the question or
further detail would reproduce code.

Each new document needs a clear title, concise summary, Responsibility section,
and only useful additional sections. Omit empty sections. Put repository-backed
claims under Observed and include an evidence baseline comment:
<!-- specspine:evidence-baseline source=<revision>; inspected=<YYYY-MM-DD> -->
Keep uncertain interpretations under Inferred and unresolved matters under
Open questions. Never manufacture accepted intent.

Use final-live-location relative links without URL fragments. Create semantic
IDs only when useful; use `(DEC|CON|OBS|INF|OQ)-[a-z0-9]+` with optional
lowercase kebab suffixes. Define bold ID bullets under matching sections inside
one `specspine:semantic-ids:begin`/`end` region. Reference the exact plain ID and
its defining file; never use an ID-looking label for an ordinary relationship.

Before finishing, verify that every candidate is a regular non-symlink file,
has a non-colliding meaningful final path, cites only inspected evidence, and
can be published unchanged. Do not enumerate hypothetical security, scaling,
retry, deployment, or operational questions without repository evidence.
Stop when the assigned architectural zone is answered.

Return a compact report containing only: evidence inspected; created files and
relative final destinations; mapped responsibilities and relationships;
material follow-up architectural questions with prerequisites; unresolved
inferences or drift; and whether no useful node was found. Do not repeat the
document prose.

Repository: <repository-root>
Immutable source revision: <revision>
Live Spine, read-only: <spine-root>
Shared repository topology: <topology-snapshot>
Existing architecture ownership: <ownership-summary>
Applicable project instructions: <project-instructions>

Assignment:
Writable output root: <private-staging-root>
Final namespace: <relative-destination>
Architectural zone and question: <one-zone>
```

For a producer failure covered by the retry policy above or an unusable result,
preserve diagnostics, discard only incomplete staging, requeue the question
once, and refill capacity. After a repeated confirmed failure, continue
independent work and report it as incomplete.

## Consume and publish results

As soon as each producer finishes, consume its report and inspect every reported
candidate file once. Do not inspect repository source or repeat evidence
validation. Check that the candidate:

- is a regular, non-symlink Markdown file inside its staging root;
- has a normalized destination inside `<spine-root>`, is not `README.md`, and
  does not overwrite an existing path;
- is a publishable specification for the assigned architectural question, not
  an assessment, plan, integration note, empty template, or obviously malformed
  artifact;
- contains a useful summary and responsibility, baselines `Observed` claims,
  and uses valid final-location links and semantic IDs;
- does not conflict with its assigned ownership or an obvious owner in the
  current architecture index and relevant linked specifications.

This is a bounded acceptance read, not source-aware integration or a whole-Spine
audit. Do not merge, semantically rewrite, or selectively copy candidate
content. Return a rejected candidate as a focused correction question; if its
producer is no longer available, enqueue the correction like other ready work.
Keep its staging path recorded until corrected or explicitly failed. Do not
leave the freed producer slot idle while that correction is pending.

Publish each acceptable candidate unchanged to the same relative destination
under `<spine-root>` using an available filesystem move/rename tool, for example
`mv` through a shell tool. Create only a needed destination directory; never
reconstruct the file by reading its contents and writing a new copy, and do not
reread it after the move. Never overwrite. A path collision becomes a focused
correction question that chooses a different meaningful path and updates its
own links; never add an arbitrary numeric suffix.

Staged publication is intentionally exempt from the ordinary requirement
to make every new node reachable from the architecture index during the same
operation. Defer navigation cleanup until the single post-saturation
normalization.

Remove each empty staging root immediately after its files are moved. When
possible, perform the move, empty-root removal, and append-only publication
checkpoint in one filesystem tool call. Do not reread the ledger afterward.
Never leave staged copies as a second architecture source.

## Continue to saturation

Perform planning incrementally from completion reports without pausing active
workers. Reach saturation only when:

- the ready queue is empty;
- no producer is active;
- every blocked question is either resolved, moved to ready, or explicitly
  deferred because it requires authority or unavailable evidence; and
- completion reports reveal no material independent architectural gap worth
  another producer.

For a whole-repository request, use completion reports to cover system topology
and material cross-cutting runtime, data, integration, deployment,
configuration, security, and observability flows. Enqueue one zone-specific
coverage probe for each material uncovered area; do not turn checklist items
inside one zone into separate producers. The orchestrator must not deeply
inspect source to answer them in subagent mode.

Do not invoke SpecSpine Doctor during the mapping run, including between
producer completions. Do not normalize or reorganize the live Spine while any
producer is active or any question remains ready or resolvably blocked.

## Normalize once after saturation

After saturation, perform one sequential normalization using only the ledger,
producer reports, and files under `<spine-root>`; do not inspect repository
source. Treat published destination paths in the ledger as the new-node
inventory. Do not reread every published specification or load the complete
Spine contents:

1. Keep the established namespace layout when it remains adequate.
2. Use producer reports and destination paths to decide whether stable cohesive
   clusters already justify the few broad namespaces planned during the run.
   If not, keep the current layout. Never mirror the source tree.
3. Read `README.md` and only documents whose paths or links must change. Move
   specifications only when navigation would otherwise remain materially
   difficult.
4. Update affected relative links and curated `README.md` navigation so every
   specification is reachable.
5. Preserve architectural prose, accepted intent, evidence baselines, semantic
   IDs, unconfirmed inferences, and open questions. Do not merge, reject,
   reinterpret, or otherwise semantically rewrite producer output.
6. Verify affected links and semantic-ID references.

This normalization is part of completing a large-repository Map request and
needs no separate prompt. Perform it once, not during continuous mapping.
When tooling permits, batch the final deterministic check, source-fingerprint
verification, successful run-root deletion, and final source-state verification
into one conditional filesystem command rather than separate model/tool cycles.

## Optional post-map Doctor

Invoke SpecSpine Doctor only when the current request explicitly includes a
post-map semantic review. Run it once after saturation, normalization, and
mechanical checking. Ask it to inspect the complete normalized `<spine-root>`
without repository source and propose one exact repair batch, identifying
authority-dependent decisions. Apply semantic repairs only after operator
approval.
