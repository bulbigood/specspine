---
name: iwe-spec-audit
description: Audit Specspine v5 format conformance and semantic readiness through IWE without changing files. Use for workspace health checks, readiness review, blocker and semantic-ID integrity, exhaustive-boundary authority, asset validation, completeness honesty, or preflight before verification and implementation.
---

# IWE Spec Audit

Perform a read-only audit. Do not repair specifications, implementation, tests,
or configuration.

Find an available skill whose description covers IWE projects and document
operations, read it, and delegate every interaction with IWE to it. State the
result needed from IWE; do not prescribe commands, flags, syntax, traversal,
batch sizes, token budgets, or compatibility handling. If no applicable IWE
skill is available, report the missing capability and stop.

Use [semantic audit](references/specspine-audit.md) as the audit contract. Read
the relevant parts of [Specspine format](references/specspine-format.md) and
[Specspine semantics](references/specspine-semantics.md) when a finding depends
on document structure, authority, ownership, or readiness. Treat the workspace
Specspine schema as the executable document contract.

Ask the selected IWE skill for:

1. the applicable project and Markdown library;
2. the Specspine schema-validation result;
3. every selected Specspine v5 owner, including its key, required frontmatter,
   assets, and complete document content;
4. task-relevant relationships when closure-level rules apply;
5. explicit omissions or truncation from the requested scope.

Choose whole-workspace or explicitly task-bounded scope. Apply every required
semantic and filesystem check without treating accepted intent as evidence that
a document passes. Continue safely evaluable checks after schema errors when
useful, but keep readiness invalid until the schema gate passes.

Return the audit report contract from the reference, including `none` for empty
finding classes and confirmation that no files changed.
