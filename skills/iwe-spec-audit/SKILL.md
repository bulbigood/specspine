---
name: iwe-spec-audit
description: Audit Specspine v5 format conformance and semantic readiness through native IWE projections without changing files. Use for workspace health checks, readiness review, blocker and semantic-ID integrity, exhaustive-boundary authority, asset validation, completeness honesty, or preflight before verification and implementation.
---

# IWE Spec Audit

Perform a read-only audit. Do not repair specifications, implementation, tests,
or configuration.

Use the installed official `iwe-memory-system` skill for every IWE operation and
read it before continuing. If it is unavailable, stop and direct the operator to
the Specspine README setup. Treat its CLI examples as guidance that may lag the
installed IWE binary. If a command rejects an argument or prints a deprecation
warning, run `iwe <command> --help`, switch to the installed syntax, and do not
retry the known-stale form.

Before auditing, read [Specspine format](references/specspine-format.md),
[Specspine semantics](references/specspine-semantics.md), and
[semantic audit](references/specspine-audit.md) completely. Read and apply
[IWE operations](references/specspine-operations.md) before discovery or
projection. The workspace
`.iwe/schemas/specification.yaml` remains the executable document contract.

1. Resolve the applicable IWE project root and `library.path`; treat incomplete
   Specspine configuration as setup failure and ask the operator to run
   `iwe-spec-setup`. If it is unavailable, point to the README manual fallback.
   Do not install or repair setup from this workflow.
2. Select whole-workspace or explicitly task-bounded scope. Do not silently claim
   whole-workspace coverage for a sample.
3. Run the IWE compatibility gate and `iwe schema validate`, then project all selected owners exactly as defined
   by the audit reference. Use bounded batches for a large workspace.
4. Apply every required semantic and filesystem check. Do not infer accepted
   intent to make a document pass.
5. Return the audit report contract from the reference, including `none` where a
   finding class is empty and confirming that no files changed.

Schema errors do not authorize repair. Continue with safely evaluable semantic
checks when useful, but mark readiness invalid until the schema gate passes.
