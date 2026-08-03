---
name: iwe-spec-verify
description: Verify implementation conformance against Specspine v5 contracts retrieved through IWE. Use for implementation-independent criteria checks, code/spec comparison, external-boundary audits, and evidence-backed conformance reports.
---

# IWE Spec Verify

Use the installed official `iwe-memory-system` skill for every IWE operation
and read it before continuing. If it is unavailable, stop and direct the
operator to the Specspine README setup.

Treat its CLI examples as guidance that may lag the installed IWE binary. If a
command rejects an argument or prints a deprecation warning, run
`iwe <command> --help`, switch to the syntax reported by the installed CLI, and
do not retry the known-stale form.

Before interpreting or verifying Specspine documents, read
[Specspine format](references/specspine-format.md),
[Specspine semantics](references/specspine-semantics.md), and
[Specspine conformance](references/specspine-conformance.md) completely. Read
and apply [IWE operations](references/specspine-operations.md) before discovery
or retrieval. Also
read and apply [semantic audit](references/specspine-audit.md) to the selected
owners before evaluating implementation conformance. The
workspace `.iwe/schemas/specification.yaml` is the executable contract for exact
document structure; the references define authority, boundaries, and finding
classification.

Resolve the applicable IWE project root as defined by the format reference
before running any IWE command. Use that root as the working directory and read
its `.iwe/config.toml` once to determine `library.path`. Treat unavailable IWE
or missing required Specspine configuration as an incomplete setup: stop and
ask the operator to run `iwe-spec-setup`. If that skill is unavailable, point
to the README manual fallback. Do not install or repair setup from this
workflow. Verify is a read-only reasoning workflow; there is no `iwe verify`
command.

1. Run the IWE compatibility gate and `iwe schema validate`; stop on schema
   errors or missing required CLI features.
2. Apply the semantic audit gate to the selected owners. Stop on audit errors or
   when a relevant blocker makes the intended behavior materially ambiguous.
3. Retrieve the owner and task-relevant graph closure with deliberate expansion
   directions and hard document/token budgets. Report inclusion and exclusion
   decisions and any truncation uncertainty.
   Aggregate implementation freedom using the strictest applicable governing
   owner and record which owner introduced it.
4. Treat `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, `VER`, and assets marked
   `normative: true` as authority.
5. Treat `OBS`, `INF`, and non-normative assets only as evidence.
6. Compare implementation-independent criteria and other accepted claims with
   code, tests, runtime behavior, and registered assets.
7. Classify and report findings using the conformance reference. Record whether
   every governing owner declares `coverage.external-boundary: exhaustive` with
   a valid owner-local `CON-*` basis.
8. Do not modify specifications, implementation, tests, or configuration.

Run a focused test only when it directly establishes a retrieved claim and is
not expected to rewrite project files. A concrete static call-path trace is
sufficient to establish an external interaction. Do not run unrelated tests or
lint merely to strengthen a classification.

## Report contract

Return one compact conformance report:

1. `Scope` — seed, included governing owners with reasons, relevant exclusions,
   aggregated implementation freedom and its constraining owners, boundary
   coverage, and retrieval truncation if any.
2. `Findings` — each classification, claim or normative prose, expectation,
   concrete evidence, and confidence; use `none` when empty.
3. `Checks` — exact tests or inspections and `passed`, `failed`,
   `environment-blocked`, or `not-run`.
4. `Verdict` — remaining divergence and confirmation that Verify changed no
   project files.

When Verify surrounds implementation, do not repeat two full reports. Return
the initial findings, final findings, and explicit finding transitions over the
same declared scope.
Schema validity does not prove implementation conformance.
