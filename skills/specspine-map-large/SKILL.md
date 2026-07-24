---
name: specspine-map-large
description: Orchestrate a deliberate end-to-end mapping run for a large brownfield repository using a bounded backlog, isolated staged producers, continuous publication, recovery checkpoints, saturation, and final normalization. Use only when the operator explicitly invokes $specspine-map-large for complete or sustained repository mapping; do not infer this mode from repository size or an ordinary mapping request. Works with concurrent producers or one local producer. Do not use for a focused survey, subsystem map, deepening, or refresh (use specspine-map).
---

# SpecSpine Map Large

Orchestrate a complete large-repository Map run. Keep the mapping and
publication contract identical whether producers run concurrently or the
current agent performs every role sequentially.

## Resources

- Read [references/orchestration.md](references/orchestration.md) completely
  before starting or resuming a run. It owns scheduling, staging, publication,
  recovery, producer-command composition, saturation, normalization, and
  optional post-map Doctor behavior.
- Run `scripts/bundle_skill.py --print` once with the installed
  `specspine-map` root and a file under the disposable run root. The generic
  script strips Map frontmatter, concatenates its complete body with every
  UTF-8 file under Map `references/`, saves the result, and returns that same
  complete bundle in the tool output. Do not read the generated file afterward.
  Embed the returned bundle in every producer command. Producers must not load
  skills, references, or templates themselves.

## Scope

Use this skill only through explicit operator selection. Do not activate it
merely because a repository appears large or a normal Map request contains
several areas.

Own orchestration, not architectural invention. Repository evidence may
establish observations and support inferences, but never establishes accepted
decisions or constraints. Do not modify production code, claim complete
code/spec conformance, or apply semantic Doctor repairs without approval.

## Workflow

1. Resolve the repository root and `<spine-root>`. Use exactly one path-only
   project-tree listing—the exact `find` command specified by
   `references/orchestration.md`—to seed the bounded backlog from directory and
   file names, including the paths of existing Spine documents. Do not read
   source, tests, configuration, or existing Spine contents during initial
   planning.
2. Follow `references/orchestration.md` as the execution contract.
3. Send each worker the complete self-contained producer command composed from
   the generated Map instruction bundle, staging contract, source revision,
   read-only live Spine, private writable output root, final namespace, shared
   topology/ownership context, and exactly one coherent architectural zone with
   its question.
4. When concurrent producers are unavailable, execute the same inline producer command
   locally for one queued question at a time, then return to the same consumer,
   checkpoint, saturation, and normalization loop. The current agent is
   orchestrator, producer, and consumer; only concurrency changes.
5. Report source state, execution limitation when sequential, published files,
   mapped areas, failed or deferred questions, unconfirmed inferences,
   unresolved drift, normalization, mechanical-check results, and qualitative
   remaining coverage.

An explicit invocation approves staged mapping, mechanical publication, and the
single post-saturation normalization. Ask only before changing accepted intent,
choosing among materially different canonical owners, or applying proposed
semantic repairs.
