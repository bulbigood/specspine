---
name: iwe-spec-verify
description: Verify implementation conformance against Specspine v5 contracts retrieved through IWE. Use for implementation-independent criteria checks, code/spec comparison, external-boundary audits, and evidence-backed conformance reports.
---

# IWE Spec Verify

Use the installed official `iwe-memory-system` skill for every IWE operation
and read it before continuing. If it is unavailable, stop and direct the
operator to the Specspine README setup.

Before interpreting or verifying Specspine documents, read
[Specspine format](references/specspine-format.md),
[Specspine semantics](references/specspine-semantics.md), and
[Specspine conformance](references/specspine-conformance.md) completely. The
workspace `.iwe/schemas/specification.yaml` is the executable contract for exact
document structure; the references define authority, boundaries, and finding
classification.

Resolve the applicable IWE project root as defined by the format reference
before running any IWE command. Use that root as the working directory and read
its `.iwe/config.toml` once to determine `library.path`. Treat unavailable IWE
or missing required Specspine configuration as an incomplete setup: stop and
point to the README instead of installing or repairing it. Verify is a
read-only reasoning workflow; there is no `iwe verify` command.

1. Run `iwe schema validate`; stop on schema errors.
2. Check owner-local ID uniqueness and blocker targets. Stop when a relevant
   blocker makes the intended behavior materially ambiguous.
3. Retrieve the owner and task-relevant graph closure with `iwe retrieve`.
4. Treat `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, `VER`, and assets marked
   `normative: true` as authority.
5. Treat `OBS`, `INF`, and non-normative assets only as evidence.
6. Compare implementation-independent criteria and other accepted claims with
   code, tests, runtime behavior, and registered assets.
7. Classify and report findings using the conformance reference. Record whether
   every governing owner declares `coverage.external-boundary: exhaustive`.
8. Do not modify specifications, implementation, tests, or configuration.

Run a focused test only when it directly establishes a retrieved claim and is
not expected to rewrite project files. A concrete static call-path trace is
sufficient to establish an external interaction. Do not run unrelated tests or
lint merely to strengthen a classification.

## Report contract

Return these sections even when one contains `none`:

1. Scope — retrieved owners and governing boundary coverage.
2. Claims checked — normative IDs, normative assets, and criteria.
3. Findings — classified entries with expectation and evidence.
4. Test evidence — exact checks and `passed`, `failed`,
   `environment-blocked`, or `not-run` status.
5. Verdict — conformance, remaining divergence, and confirmation that the
   verification phase intentionally changed no project files.

When Verify surrounds an implementation, return separate `Pre-change Verify`
and `Post-change Verify` contracts followed by explicit finding transitions.
Schema validity does not prove implementation conformance.
