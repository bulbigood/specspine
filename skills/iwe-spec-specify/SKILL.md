---
name: iwe-spec-specify
description: Create or refine accepted durable software specifications in a Specspine v5 IWE library. Use for greenfield intent, requirements and architecture changes, impact analysis, and restructuring accepted specifications.
---

# IWE Spec Specify

Work only with accepted intent.

Find an available skill whose description covers IWE projects and document
operations, read it, and delegate every interaction with IWE to it. State the
result needed from IWE; do not prescribe commands, flags, syntax, traversal,
batch sizes, token budgets, or compatibility handling. If no applicable IWE
skill is available, report the missing capability and stop.

Load [Specspine format](references/specspine-format.md) and
[Specspine semantics](references/specspine-semantics.md) together in one
reference-reading tool call before interpreting or changing an owner. Defer
[semantic audit](references/specspine-audit.md) until there are changed owners,
then read it once and apply it to the whole batch before claiming readiness.
Treat the workspace Specspine schema as the executable document contract.

Ask the selected IWE skill to resolve the applicable project and library, verify
the Specspine setup, find plausible canonical owners, and retrieve only the
task-bounded accepted-intent closure. Require explicit omissions or truncation.
If setup is incomplete, report that condition without repairing it here.

1. Update the canonical owner; do not copy claims between owners.
2. Apply the `refine` versus `expand` owner test from the semantics reference.
   Create an owner only when it has an independent durable boundary and record
   why plausible existing owners do not govern it.
3. Distinguish structural inclusion from non-structural reference according to
   the format contract.
4. Give the selected IWE skill the intended owner-level result and require it to
   perform all creation, updates, renames, removals, decomposition, inlining,
   relationship maintenance, and validation through IWE.
5. Apply the semantic audit gate to every changed owner. Do not report readiness
   while errors introduced by the batch remain.

A new topic is not automatically a new owner. Statement IDs are owner-local;
refine a matching claim instead of creating a near duplicate. A blocking
`OQ-*` must exist in the same owner and appear in its `blockers` metadata.
Evidence and non-normative assets cannot support facet advancement.

Do not invent relationship metadata, generated indexes, lifecycle state, or
other structures that duplicate IWE.
