---
name: specspine-map-large
description: Orchestrate a deliberate end-to-end mapping run for a large brownfield repository using a bounded backlog, staged producers, continuous publication, recovery checkpoints, saturation, and final normalization. Use only when the operator explicitly invokes $specspine-map-large for complete or sustained repository mapping; do not infer this mode from repository size or an ordinary mapping request. Works with parallel subagents or one local producer. Do not use for a focused survey, subsystem map, deepening, or refresh (use specspine-map).
---

# SpecSpine Map Large

Orchestrate a complete large-repository Map run. Keep execution logic identical
whether mapping producers run concurrently or the current agent performs every
role sequentially.

Require `$specspine-map` in the same environment. If it is unavailable, report
the missing mapper dependency instead of reconstructing its workflow inside
this skill.

## Resources

- Read [references/orchestration.md](references/orchestration.md) completely
  before starting or resuming a run. It owns scheduling, staging, publication,
  recovery, saturation, normalization, and optional post-map Doctor behavior.
- Read [references/spec-semantics.md](references/spec-semantics.md) before
  accepting mapped claims or acting as a local mapping producer.
- Read [references/spec-format.md](references/spec-format.md) before bootstrap,
  candidate acceptance, or normalization.
- Read [references/mapping-method.md](references/mapping-method.md) before the
  shallow topology survey or when acting as a local mapping producer.
- Use templates under `assets/templates/` when this agent must create an index
  or specification.

## Scope

Use this skill only through explicit operator selection. Do not activate it
merely because a repository appears large or a normal Map request contains
several areas.

Own orchestration, not architectural invention. Repository evidence may
establish observations and support inferences, but never establishes accepted
decisions or constraints. Do not modify production code, claim complete
code/spec conformance, or apply semantic Doctor repairs without approval.

## Workflow

1. Resolve the repository root and `<spine-root>`. Read the current architecture
   index and only enough repository topology to seed the bounded backlog.
2. Follow `references/orchestration.md` as the execution contract.
3. Assign every bounded mapping question to `$specspine-map`. Supply its source
   revision, read-only live Spine, private writable output root, final namespace,
   and exact architectural question.
4. When subagents are unavailable, apply `$specspine-map` locally to one queued
   question at a time, then return to the same consumer, checkpoint, scheduling,
   saturation, and normalization loop. The current agent is orchestrator,
   producer, and consumer; only concurrency changes.
5. Report source state, execution limitation when sequential, published files,
   mapped areas, failed or deferred questions, unconfirmed inferences,
   unresolved drift, normalization, mechanical-check results, and qualitative
   remaining coverage.

An explicit invocation approves staged mapping, mechanical publication, and the
single post-saturation normalization. Ask only before changing accepted intent,
choosing among materially different canonical owners, or applying proposed
semantic repairs.
