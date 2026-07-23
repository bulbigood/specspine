# Parallel brownfield mapping

Use parallel mapping to shorten discovery for a large repository with several
independent architectural areas. Preserve iterative breadth-before-depth
mapping: parallelism changes execution, not the standard for creating a useful
specification.

## Preconditions

- Resolve and read the live `<spine-root>`.
- Perform or confirm a breadth-first survey before deep parallel work.
- Use a source revision that remains stable for the entire wave.
- Use ordinary sequential mapping when subagents are unavailable or the
  remaining questions overlap too heavily for independent investigation.

Do not use a requested or desired document count to plan areas, worker prompts,
splits, or stopping decisions.

## Plan a wave

Inspect the repository shape and current Mapping status. Build a bounded list
of architectural questions, not directory assignments. Each question should
have:

- a durable responsibility, runtime boundary, cross-cutting flow, or ownership
  problem to investigate;
- a disjoint primary evidence scope, while allowing workers to inspect
  integration edges;
- enough independence that another worker can proceed without its output;
- an explicit reminder to stop before reproducing implementation detail.

Do not assign two workers competing ownership of the same concept. Keep
uncertain overlaps for source-aware integration rather than resolving them in
worker prompts.

Use the largest safe concurrency:

```text
min(available worker slots, independent questions, safe repository I/O)
```

The orchestrator is the only agent allowed to spawn mapping workers. Workers
must not spawn further workers. Prefer several bounded waves over one exhaustive
fan-out so later plans can use earlier findings.

## Isolate worker writes

Create one disposable staging root per worker outside the live
`<spine-root>`. Give every worker:

- the repository root and immutable source revision;
- the live `<spine-root>` as read-only context;
- its private staging root as the only writable documentation location;
- one architectural question;
- the Map skill and applicable project instructions.

Workers may read existing specifications to avoid duplicate ownership, but
must not modify the repository, the live Spine, another worker's staging root,
or `README.md`. They create only candidate specification nodes in their private
staging root.

Do not preallocate a number of documents. A worker may create no document when
the live Spine already answers the question or further detail would reproduce
code. If a candidate path already exists inside its staging root, choose
another meaningful concept name and report the final path; never overwrite it
or add an arbitrary numeric suffix.

Require each worker to report:

- evidence inspected;
- candidate files created;
- mapped responsibilities and relationships;
- possible overlap with live or sibling concepts;
- unconfirmed inferences and open questions;
- whether no useful new node was found.

Before integration, verify mechanically that the source tree and live Spine
retain their pre-wave hashes. Treat any worker mutation outside its staging root
as a failed worker result.

## Integrate with Map

After all workers finish, the orchestrator performs one source-aware Map
integration. Read every candidate, the relevant live specifications, and
representative source evidence needed to resolve overlaps.

During integration:

1. Reject candidates that lack a durable responsibility or adequate evidence.
2. Merge duplicate candidate content and keep one canonical owner.
3. Prefer enriching an existing owner over importing a competing owner.
4. Split only independently evolving responsibilities.
5. Choose stable filenames and rewrite candidate links to final paths.
6. Add useful direct relationships and keep every imported node reachable.
7. Update overview nodes and the architecture index without turning the index
   into an exhaustive file list.
8. Introduce only a few broad namespaces when the flat collection is hard to
   scan; normally add at most one directory layer and never mirror source
   layout.
9. Preserve accepted decisions, constraints, external semantic-ID references,
   unresolved conflicts, and unrelated content.

The parallel mapping request authorizes organizing newly generated
repository-backed observations and inferences. It does not authorize changing
accepted intent, silently resolving an open question, or discarding a conflict
between accepted intent and repository evidence.

## Audit and continue

After integration, invoke SpecSpine Doctor with an explicit request to inspect
the whole integrated Spine and:

- the deterministic whole-Spine checker;
- semantic review of duplicate ownership, fragmentation, stale overview text,
  hidden direct relationships, and excessive implementation detail;
- a concrete repair batch for any unambiguous mechanical or semantic defects.

Pass the integrated `<spine-root>` and this review scope in the Doctor request.
Doctor must ask the operator to approve its proposed repair batch before it
writes. Do not require Doctor itself to know how the documents were produced.
Doctor does not inspect repository code; resolve source-dependent ownership or
decomposition through Map before invoking it.

Use a request equivalent to:

```text
Progressively review the whole SpecSpine at <spine-root>. Run the deterministic
checker, then inspect every specification for duplicate ownership, unnecessary
fragmentation, stale overview text, hidden direct relationships, and excessive
implementation detail. Propose an exact repair batch for unambiguous defects
that preserve meaning and ask the operator to approve it before writing. Report
any ownership or boundary decision that still requires authority. Do not
inspect repository files outside the SpecSpine.
```

Keep staging roots until integration and the Doctor audit succeed. Then discard
them as temporary mapping artifacts; never leave them as a second architecture
source.

Run another wave only for material gaps identified after integration. Stop when
the requested questions are answered and additional reading has low
architectural value. When an external process uses repeated no-change runs as a
saturation signal, distribute those runs across distinct areas and
cross-cutting flows; repeated probes of one mature area do not establish
whole-repository saturation.
