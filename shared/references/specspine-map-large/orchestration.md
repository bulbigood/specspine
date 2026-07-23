# Large-repository mapping orchestration

Use one continuous mapping protocol for a large repository. Run several
subagent producers when available or one sequential local producer otherwise.
Parallelism changes throughput, not planning, publication, recovery, or the
standard for a useful specification.

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
staging roots and a small durable ledger there. Record the source identifier,
ready, active, blocked, failed, and completed questions, plus published
destination paths. Update it after every state transition. On resume, reconcile
published paths, return interrupted active questions to ready, and continue.
Delete the run root after successful completion. If the run stops incomplete,
preserve and report its location for resumption.

Inspect only enough repository shape and current Mapping status to seed the run.
Do not deeply explore the codebase or enumerate every possible area up front.
Build only enough ready architectural questions to fill current producer
capacity plus a small reserve. Extend this bounded backlog from producer
reports. Each question should have:

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

```text
min(actual worker slots, independent ready questions, safe repository I/O)
```

Reserve orchestrator capacity when the environment counts it in the total
concurrency limit. Assume available repository I/O is safe unless a documented
limit or observed contention requires less concurrency; report any reduction.
The orchestrator is the only agent allowed to spawn mapping workers. Workers
must not spawn further workers.

## Schedule as producer-consumer

Maintain one continuous dependency-aware ready queue, active worker set, and
blocked-question set. Keep the backlog bounded to material architectural
questions, not a requested document count. A completed producer report is the
primary discovery mechanism: add its material adjacent areas and cross-cutting
questions to ready or blocked without rereading repository source.

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

Do not wait for all active workers to finish while a ready question and a safe
worker slot are available. Keep active concurrency at the largest safe level
until no question is ready. Candidate acceptance and publication must not
precede refilling a safe slot. If the environment cannot launch a replacement
before consuming the completed result, treat that ordering as a transport
limitation and report it; never choose it as the orchestration policy.

If the environment exposes only barrier-style batch completion or cannot refill
slots safely, use its barrier primitive as a transport limitation and report
that limitation; do not introduce conceptual waves or delay already-ready work
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
root. Give every subagent worker:

- the repository root and immutable source revision;
- the live `<spine-root>` as read-only context;
- its private staging root as the only writable documentation location;
- the relative destination under `<spine-root>` represented by that staging
  root;
- the final namespace assigned to its architectural question;
- one architectural question;
- `$specspine-map` and applicable project instructions.

Workers may read existing specifications to avoid duplicate ownership, but
must not modify the repository, the live Spine, another worker's staging root,
or `README.md`. They create only publish-ready specification nodes in their
private staging root. Do not create assessments, reviews, integration notes, or
other artifacts that are not intended to become live specifications.

Each producer owns source validation and the complete quality of its files.
Before finishing, it must:

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

Require each producer to report:

- evidence inspected;
- publish-ready files created and their relative destination paths;
- mapped responsibilities and relationships;
- material follow-up architectural questions and their prerequisites;
- unconfirmed inferences and open questions;
- whether no useful new node was found.

If a producer terminates or returns an unusable result, preserve diagnostic
information in the ledger, discard only its disposable incomplete staging,
requeue the question once, and refill capacity. After a repeated failure,
record it as failed, continue independent work, and report it as incomplete.

## Consume and publish results

As soon as each producer finishes, consume its report and inspect every reported
candidate file once. Do not inspect repository source or repeat evidence
validation. Check that the candidate:

- is a regular, non-symlink Markdown file contained by its staging root;
- has a normalized relative destination contained by `<spine-root>`, is not
  `README.md`, and does not overwrite an existing path;
- is a publishable specification for the assigned architectural question, not
  an assessment, plan, integration note, empty template, or obviously malformed
  artifact;
- contains a useful summary and responsibility, gives `Observed` claims an
  evidence baseline, and uses final-location relative links;
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

Remove each empty staging root immediately after its files are moved. Record
publication in the ledger before reusing capacity. Never leave staged copies as
a second architecture source.

## Continue to saturation

Perform planning incrementally from completion reports without pausing active
workers. Reach saturation only when:

- the ready queue is empty;
- no producer is active;
- every blocked question is either resolved, moved to ready, or explicitly
  deferred because it requires authority or unavailable evidence; and
- completion reports reveal no material independent architectural gap worth
  another producer.

For a whole-repository request, ensure completion reports have covered the
system topology and material cross-cutting runtime, data, integration,
deployment, configuration, security, and observability flows. Enqueue a bounded
coverage-probe question for any class not assessed; the orchestrator must not
deeply inspect source to answer it in subagent mode. When an external process
uses repeated no-change runs as a saturation signal, distribute those probes
across distinct areas and flows.

Do not invoke SpecSpine Doctor during the mapping run, including between
producer completions. Do not normalize or reorganize the live Spine while any
producer is active or any question remains ready or resolvably blocked.

## Normalize once after saturation

After saturation, perform one sequential normalization using only files under
`<spine-root>`; do not inspect repository source. Inventory the complete live
SpecSpine, run the deterministic checker when available, and process documents
progressively by current namespace so the complete contents need not remain in
context at once:

1. Keep the established namespace layout when it remains adequate.
2. If the flat namespace is difficult to navigate and stable cohesive clusters
   are now visible, move specifications into a few broad lowercase kebab-case
   directories, normally with at most one directory layer. Never mirror the
   source tree.
3. Update affected relative links and curated `README.md` navigation so every
   specification is reachable.
4. Preserve architectural prose, accepted intent, evidence baselines, semantic
   IDs, unconfirmed inferences, and open questions. Do not merge, reject,
   reinterpret, or otherwise semantically rewrite producer output.
5. Verify affected links and semantic-ID references, then rerun the
   deterministic SpecSpine checker when it is available.

This normalization is part of completing a large-repository Map request and
needs no separate prompt. Perform it once, not during continuous mapping.

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
