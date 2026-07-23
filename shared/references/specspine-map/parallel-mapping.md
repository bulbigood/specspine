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

Do not assign two workers competing ownership of the same concept. Resolve
uncertain assignment overlap before spawning; there is no semantic integration
stage after workers finish.

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
- the relative destination under `<spine-root>` represented by that staging
  root;
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
- unconfirmed inferences and open questions;
- whether no useful new node was found.

## Publish the wave

After all workers finish, mechanically move every publish-ready file from its
private staging root to the same relative path under `<spine-root>`. Do not read
or review file contents, inspect repository source, repeat evidence validation,
compare ownership, merge or reject documents, rewrite content or links, update
existing specifications, update `README.md`, run SpecSpine Doctor, or run a
whole-Spine audit. Worker output is the published output.

Before moving, compare destination path names only. Never overwrite an existing
live file or another worker's destination. Return a colliding file to its worker
to choose a different meaningful path, then publish it unchanged. This is a
mechanical collision check, not semantic integration.

Raw parallel publication is intentionally exempt from the ordinary requirement
to make every new node reachable from the architecture index during the same
operation. Navigation cleanup, semantic consolidation, and integrity review are
separate explicitly requested operations.

Remove empty staging roots after their files are moved. Never leave staged
copies as a second architecture source.

Run another wave only for material gaps identified after publication. Stop when
the requested questions are answered and additional reading has low
architectural value. When an external process uses repeated no-change runs as a
saturation signal, distribute those runs across distinct areas and
cross-cutting flows; repeated probes of one mature area do not establish
whole-repository saturation.
