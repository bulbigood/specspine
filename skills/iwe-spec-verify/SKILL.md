---
name: iwe-spec-verify
description: Verify implementation conformance against Specspine v5 contracts retrieved through IWE. Use for implementation-independent criteria checks, code/spec comparison, external-boundary audits, and evidence-backed conformance reports.
---

# IWE Spec Verify

Run a read-only reasoning workflow. Do not change specifications,
implementation, tests, or configuration.

Find an available skill whose description covers IWE projects and document
operations, read it, and delegate every interaction with IWE to it. State the
result needed from IWE; do not prescribe commands, flags, syntax, traversal,
batch sizes, token budgets, or compatibility handling. If no applicable IWE
skill is available, report the missing capability and stop.

Use [Specspine conformance](references/specspine-conformance.md) as the finding
contract. Read the relevant parts of [Specspine format](references/specspine-format.md),
[Specspine semantics](references/specspine-semantics.md), and
[semantic audit](references/specspine-audit.md) when the selected claims require
them. Treat the workspace Specspine schema as the executable document contract.

Ask the selected IWE skill for the applicable project and library, schema result,
selected canonical owner, task-relevant governing closure, accepted claims,
registered assets, implementation-freedom declarations, boundary coverage, and
explicit omissions or truncation. If setup is incomplete, report that condition
without repairing it.

1. Apply the semantic audit gate before conformance evaluation. Stop when errors
   or relevant blockers make required behavior materially ambiguous.
2. Treat `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, `VER`, normative prose, and
   assets marked `normative: true` as authority.
3. Treat `OBS`, `INF`, and non-normative assets only as evidence.
4. Compare accepted claims with code, tests, runtime behavior, and registered
   assets. Aggregate implementation freedom using the strictest applicable
   governing owner.
5. Classify findings through the conformance reference and record the authority
   for any exhaustive external-boundary conclusion.

Run a focused check only when it directly establishes a retrieved claim and can
be executed without project writes or external side effects. Otherwise report
it as not run or runtime-unverified. A concrete static call-path trace can
establish an external interaction.

Return one compact report with `Scope`, `Findings`, `Checks`, and `Verdict`.
Include expectation, evidence, confidence, omissions, and runtime status; use
`none` for empty findings. When Verify surrounds implementation, report initial
findings, final findings, and transitions over the same scope instead of two
full reports. Confirm that no project files changed.
