---
name: iwe-spec-implement
description: Bring an implementation into conformance with accepted Specspine v5 specifications retrieved through IWE. Use to implement missing behavior, fix code/spec divergence, satisfy verification criteria, remove explicitly conflicting behavior, or close an explicitly exhaustive external boundary.
---

# IWE Spec Implement

Change implementation, tests, and implementation-owned configuration. Never
change accepted specifications merely to make the implementation pass. Use
`conform` unless the operator selects another mode.

Use the official `iwe-memory-system` skill for every IWE operation. If it is
unavailable, obtain it from the official `iwe-org/skills` distribution through
the environment's supported skill installer and read it before continuing.

Before interpreting specifications or changing implementation, read
[Specspine format](references/specspine-format.md),
[Specspine semantics](references/specspine-semantics.md), and
[Specspine conformance](references/specspine-conformance.md) completely. The
bundled schema is the executable contract for exact document structure; the
references define authority, boundaries, finding classification, and removal
authority.

Inspect `.iwe/config.toml` and the bundled `assets/iwe` directly. Read
[IWE project setup](references/iwe-bootstrap.md) only when the Specspine
template, binding, or schema is missing or conflicting. Do not use or create a
Specspine bootstrap script.

## Modes

- `additive`: implement `missing` claims; report other findings without
  removing behavior.
- `conform` (default): implement `missing` claims and resolve `conflicting`
  behavior with a concrete normative basis.
- `closed-boundary`: apply `conform`, then remove `uncovered-boundary` behavior
  only when every governing owner declares
  `coverage.external-boundary: exhaustive`.

## Workflow

1. Resolve the operator's terms to owners with `iwe find`. Inspect neighboring
   titles only when several owners plausibly match.
2. Run `iwe schema validate`; stop on errors. Check owner-local ID uniqueness
   and blocker targets, and stop on a materially ambiguous relevant blocker.
3. Retrieve only the task-bounded closure with `iwe retrieve`.
4. Produce a complete pre-change assessment. Classify findings and distinguish
   accepted intent from evidence using the conformance and semantics references.
5. Trace each relevant normative claim to code, tests, and registered assets.
6. Apply only the finding classes authorized by the selected mode. Preserve
   unrelated behavior and use the smallest coherent change.
7. Add or update focused tests. Run the smallest relevant check, followed by a
   broader suite only when risk justifies it.
8. Run `iwe schema validate` after implementation and produce a post-change
   assessment over the same scope.

The final response must contain `Pre-change assessment`,
`Post-change assessment`, and `Finding transitions`. Each assessment contains
`Scope`, `Claims checked`, `Findings`, `Test evidence`, and `Verdict`, using
explicit `none` where applicable. Also report changed files and remaining
runtime-unverified claims.

Before any deletion authorized by the conformance reference and selected mode,
inspect callers, public interfaces, migrations, configuration, and tests.
Remove a full dead path only when safe and in scope. Do not weaken claims,
promote observations to intent, create relationship metadata, or add a graph or
lifecycle mechanism beside IWE.
