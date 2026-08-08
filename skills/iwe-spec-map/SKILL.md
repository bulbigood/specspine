---
name: iwe-spec-map
description: Map boundary-significant repository evidence into Specspine v5 documents managed by IWE. Use for brownfield surveys, focused deepening, evidence refresh, and implementation drift inspection.
---

# IWE Spec Map

Map repository evidence without turning implementation details into accepted
intent.

Find an available skill whose description covers IWE projects and document
operations, read it, and delegate every interaction with IWE to it. State the
result needed from IWE; do not prescribe commands, flags, syntax, traversal,
batch sizes, token budgets, or compatibility handling. If no applicable IWE
skill is available, report the missing capability and stop.

Read the relevant parts of [Specspine format](references/specspine-format.md)
and [Specspine semantics](references/specspine-semantics.md) before interpreting
or changing an owner. Apply [semantic audit](references/specspine-audit.md) to
every changed owner before claiming readiness. Treat the workspace Specspine
schema as the executable document contract.

Ask the selected IWE skill to resolve the applicable project and library, verify
the Specspine setup, return task-relevant owner candidates and relationships,
and retrieve only the neighborhood needed for the task. Require it to report
omissions or truncation. If setup is incomplete, report that condition without
repairing it in this workflow.

1. Select `survey`, `deepen`, `refresh`, or `drift` according to the requested
   inspection.
2. Inspect repository evidence and apply the evidence exception layer. Record a
   confirmed boundary-significant fact as owner-local `OBS-*` under
   `## Observed`; record a useful interpretation as `INF-*` under `## Inferred`.
3. Store focused inspection metadata in the owner as
   `inspection: { source: <paths>, inspected: <YYYY-MM-DD>, mode: <mode> }`.
4. Apply the owner test before creating a document: prefer `refine` when an
   existing responsibility governs the fact; choose `expand` only for an
   independently useful durable boundary. Record why plausible owners failed.
5. Give the selected IWE skill the intended owner-level changes and require it
   to perform all document creation, updates, relationship changes, and
   validation through IWE.
6. Apply the semantic audit gate to every changed owner. Do not report readiness
   while errors introduced by the batch remain.

Never promote evidence to accepted Behavior, Interfaces, Failure behavior, Data
ownership, Lifecycle, Requirements, or Verification. Evidence does not advance
a facet. Preserve existing accepted content.

In `refresh` and `drift`, keep confirmed observations, update changed facts, and
remove claims that are no longer true or exception-worthy. Assign each fact to
one canonical owner and connect cross-owner flows instead of duplicating claims.
For a combined Map → Specify task, validate the observed-only state first.

Do not create an inventory, generated index, manifest, mapping frontier,
observed-edge registry, relationship type, or graph beside IWE.
