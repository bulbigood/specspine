---
name: iwe-spec-implement
description: Bring an implementation into conformance with accepted Specspine v5 specifications retrieved through IWE. Use to implement missing behavior, fix code/spec divergence, satisfy verification criteria, remove explicitly conflicting behavior, or close an explicitly exhaustive external boundary.
---

# IWE Spec Implement

Change implementation, tests, and implementation-owned configuration. Never
change accepted specifications merely to make implementation pass. Use
`conform` unless the operator selects another mode.

Find an available skill whose description covers IWE projects and document
operations, read it, and delegate every interaction with IWE to it. State the
result needed from IWE; do not prescribe commands, flags, syntax, traversal,
batch sizes, token budgets, or compatibility handling. If no applicable IWE
skill is available, report the missing capability and stop.

Load [Specspine conformance](references/specspine-conformance.md) and
[semantic audit](references/specspine-audit.md) together in one
reference-reading tool call; they are the ordinary change-authority and
preflight contracts. Read the relevant part of
[Specspine format](references/specspine-format.md) or
[Specspine semantics](references/specspine-semantics.md) only when those
contracts do not resolve a concrete question about structure or meaning; load
both in one tool call when both are needed. Treat the workspace Specspine schema
as the executable document contract.

Ask the selected IWE skill for the applicable project and library, schema result,
selected canonical owner, task-relevant governing closure, accepted claims,
registered assets, implementation-freedom declarations, boundary coverage, and
explicit omissions or truncation. If setup is incomplete, report that condition
without repairing it.

## Modes

- `additive`: implement `missing` claims; report other findings without removal.
- `conform` (default): implement `missing` claims and resolve `conflicting`
  behavior only with concrete normative authority.
- `closed-boundary`: apply `conform`, then remove `uncovered-boundary` behavior
  only when every governing owner declares an exhaustive external boundary with
  a valid owner-local `CON-*` basis that explicitly closes it.

## Workflow

1. Apply the semantic audit gate to selected owners. Stop on errors or a
   materially ambiguous relevant blocker.
2. Produce a pre-change assessment. Aggregate implementation freedom using the
   strictest governing owner and distinguish accepted intent from evidence.
3. Trace each relevant normative claim to code, tests, and registered assets.
4. Apply only finding classes authorized by the selected mode. Preserve
   unrelated behavior and use the smallest coherent change.
5. Add or update focused tests and run checks proportional to risk.
6. Ask the selected IWE skill to return the same accepted-intent scope again
   when a fresh post-change comparison is needed; do not modify specifications.
7. Produce a post-change assessment over the same scope.

Before removing behavior, inspect callers, public interfaces, migrations,
configuration, and tests. Remove a full dead path only when safe and in scope.
Do not weaken claims, promote observations to intent, create relationship
metadata, or add a graph or lifecycle mechanism beside IWE.

Return `Scope`, `Pre-change findings`, `Changes`, `Checks`, `Finding transitions`,
and `Remaining findings and verdict`. Use `none` for empty findings and report
changed files plus runtime-unverified claims.
