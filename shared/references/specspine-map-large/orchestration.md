# Large-repository mapping orchestration

## Preconditions

- Resolve the live `<spine-root>` from project paths.
- Perform the initial survey with exactly this one path-only command; do not
  substitute another discovery command:

  ```sh
  find . -maxdepth 5 \
    \( -type d \( \
      -name .git -o -name .eval -o -name .specspine-map-run -o \
      -name node_modules -o -name .venv -o -name venv -o \
      -name .gradle -o -name .next -o -name __pycache__ -o \
      -name dist -o -name build -o -name target \
    \) \) -prune -o -print | LC_ALL=C sort
  ```

  Use only directory and file names from its output to seed the initial
  questions and identify existing Spine documents. Do not read source, tests,
  configuration, or Markdown contents during initial planning. Do not make
  another discovery call before dispatching initial ready questions.
- Capture a concise source revision and dirty-state fingerprint when available.
  Exclude `<spine-root>` and the disposable run root from the fingerprint.
  Verify that identifier before publishing results and at completion. If it
  changes, stop rather than mix evidence from different source states.

If the path listing shows that the Spine has no `README.md`, create a minimal
index and topology-level entry points before starting staged production. Do not
turn this bootstrap into repository-content inspection.

Do not use a requested or desired document count to plan areas, worker prompts,
splits, or stopping decisions.

## Initialize the run

Create one disposable run root outside the live `<spine-root>`. Keep private
staging roots and a small durable append-only ledger there. Record the source
identifier, question state changes, producer assignments, and published
destination paths. Append compact events without rereading or rewriting the
ledger during an uninterrupted run. Batch a checkpoint with the assignment or
publication filesystem operation when the environment permits. On resume, read
the ledger, reconcile published paths, return interrupted active questions to
ready, and continue. Delete the run root after successful completion. If the
run stops incomplete, preserve and report its location for resumption.

Seed the run only from the single project-tree listing. Do not inspect file
contents or read the current Mapping status during initial planning. Do not
enumerate every possible area up front. Build only a small bounded backlog of
ready architectural questions. Extend it from producer reports. Assign exactly
one coherent architectural zone to each producer. A zone may contain related
questions, but never combine independent zones merely to amortize producer
startup. Each assignment should have:

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

Run independent ready questions concurrently when the environment supports it.
Keep production within safe repository I/O limits. Execution environments own
agent lifecycle, routing, completion notification, and concurrency mechanics;
do not encode those mechanics in producer commands.

## Schedule as producer-consumer

Maintain one continuous dependency-aware ready queue and a blocked-question
set. Keep the backlog bounded to material architectural
questions. A completed producer report is the primary discovery mechanism: add
its material adjacent areas and cross-cutting questions to ready or blocked
without rereading repository source.

Consume completed results and continue ready independent work without waiting
for an entire batch. Do not introduce conceptual waves. Move a blocked question
to ready as soon as its prerequisites are satisfied. Keep questions that
require unfinished results, authority, or boundary resolution blocked rather
than speculating.

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
index, instruction, or revision discovery. Derive the initial topology and
ownership summaries only from the single path listing; an existing Spine path
means only that a document exists, not that its contents or ownership claims
are known.

Build the complete Map instruction bundle once as directed by the parent skill,
at `<run-root>/producer-instructions.md`. The builder includes every Map
reference without optional-reference filtering, saves the bundle, and emits
the same complete text. Capture that stdout directly as producer-command
context. Do not read the generated file or collect Map references manually.
Use exactly one filesystem tool call:

```text
python3 <map-large-skill-root>/scripts/bundle_skill.py \
  <map-skill-root> <run-root>/producer-instructions.md --print
```

Pass every worker the complete command below as plain text with placeholders
resolved and the bundle inserted. Keep its shared prefix byte-identical and
append producer-specific assignment fields only at the end for prompt caching.
Do not append instructions that send producers back to source skills,
references, templates, or instruction files.

```text
You are a SpecSpine mapping producer.

<complete-generated-map-instructions>

Producer execution override:

All Map instructions and references needed for this assignment are embedded
above. Do not load or invoke any skill, reference, template, or instruction
file. Inspect only evidence relevant to the assigned scope. Create
publish-ready Markdown only under the writable output root. Keep source, tests,
configuration, the live Spine, its README, and every other staging root
read-only. This execution override controls output location and publication
when the embedded general Map instructions describe live writes.
After writing the candidate and compact report, stop. Do not run a checker,
reread the candidate, or perform a final validation pass; the consumer owns all
post-production validation.

Do not omit material architectural boundaries, relationships to known owners
or overview specifications, or evidence-supported unknowns merely for brevity.
Semantic IDs remain optional; do not define one whose text merely names a path,
file, or heading.

The writable root mirrors `<spine-root>`: create every candidate at its exact
final path relative to the writable root, including the final namespace. For
example, final `jobs/runner.md` must be staged as
`<private-staging-root>/jobs/runner.md`, not
`<private-staging-root>/runner.md`. Use a non-colliding meaningful destination
that can be moved unchanged to the same relative path under the live Spine.

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
Writable output root mirroring the Spine: <private-staging-root>
Final namespace: <relative-destination>
Architectural zone and question: <one-zone>
```

For a failed or unusable producer result, preserve diagnostics and incomplete
staging. Retry once only when duplicate work cannot occur. After a repeated
failure, continue independent work and report the question as incomplete.

## Consume and publish results

As soon as each producer finishes, consume its compact report without reading
candidate prose or repository source. If it reports no useful node and staging
is empty, record that result and remove the staging root. Otherwise run the
bundled deterministic checker once against that producer's entire staging root:

```text
python3 <checker-path>/check_spine.py <spine-root> \
  --candidates <private-staging-root> --json
```

Resolve `<checker-path>` once and reuse it. Because each private staging root
mirrors the Spine, the checker evaluates every link and collision at its actual
future live path. The candidate preflight owns regular
file and symlink safety, Markdown paths, `README.md` exclusion, destination
collisions, title/summary/Responsibility structure, evidence baselines, links,
and semantic-ID mechanics against the live Spine. It ignores only deferred
index reachability and translated semantic-section names. The producer owns
source evidence and semantic fitness for its assigned zone; the orchestrator
must not repeat that work.

Candidate mode exits nonzero for any finding. Publish only after a successful
empty result. Treat findings as a focused correction question and keep its
staging path recorded until corrected or explicitly failed. Do not manually
reread, merge, semantically rewrite, or selectively copy candidate content.

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
4. Use compact producer summaries to add concise descriptions to curated
   `README.md` navigation and confirmed navigation relationships to affected
   overview documents. Update affected relative links so every specification is
   reachable. Do not infer new architecture while doing so.
5. Preserve architectural prose, accepted intent, evidence baselines, semantic
   IDs, unconfirmed inferences, and open questions. Do not merge, reject,
   reinterpret, or otherwise semantically rewrite producer output.
6. Verify affected links and semantic-ID references.

This normalization is part of completing a large-repository Map request and
needs no separate prompt. Perform it once, not during continuous mapping.
Run the full deterministic checker exactly once after normalization; do not
repeat it during cleanup. When tooling permits, batch that check,
source-fingerprint verification, successful run-root deletion, and final
source-state verification into one conditional filesystem command rather than
separate model/tool cycles.

## Optional post-map Doctor

Invoke SpecSpine Doctor only when the current request explicitly includes a
post-map semantic review. Run it once after saturation, normalization, and
mechanical checking. Ask it to inspect the complete normalized `<spine-root>`
without repository source and propose one exact repair batch, identifying
authority-dependent decisions. Apply semantic repairs only after operator
approval.
