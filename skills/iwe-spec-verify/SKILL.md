---
name: iwe-spec-verify
description: Verify implementation conformance against Specspine v5 contracts retrieved through IWE. Use for implementation-independent checks and code/spec comparison.
---

# IWE Spec Verify

Before reading IWE references or help, run the bundled
[`iwe-readiness.sh`](scripts/iwe-readiness.sh) beside this skill (add
`--descendants` only for a task spanning packages), then
compare any existing `templates.specification`, `schemas.specification`, and
schema file with the bundled assets or the protocol's allowed scoped binding.
Use the exact absolute asset paths printed by the script; do not rediscover
them with `find`. Complete this comparison before any IWE query or mutation.
Read the
[IWE bootstrap protocol](references/iwe-bootstrap.md) if anything is missing,
different, ambiguous, or conflicts with the requested path. Do not change
documents until that protocol resolves the condition. An existing
`library.path` different from the bundled fallback is authoritative, not a
collision. At the first real mismatch, read the bootstrap protocol immediately;
do not read other IWE references or query the library first.

When the workspace is ready, use the official `iwe-memory-system` skill for
all IWE operations. If it is unavailable, obtain it from the official
`iwe-org/skills` distribution through the environment's supported
skill-installation mechanism. Read only the skill and task-relevant references
before the first IWE operation. Use targeted command help only after syntax is
rejected or remains unknown; do not preload full help screens. The main
`iwe-memory-system` skill is sufficient for routine `find` and `retrieve`
operations whose syntax is already established. Verify is a reasoning and
report workflow; do not look for or invoke an `iwe verify` command.

1. Run `iwe schema validate`; stop on schema errors.
2. Retrieve the owner and relevant IWE graph closure with `iwe retrieve`.
3. Treat `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, and `VER` as normative.
4. Treat `OBS` and `INF` as evidence, never authority.
5. Evaluate implementation-independent verification criteria and registered
   assets listed in document frontmatter.
6. Emit findings as `conforming`, `missing`, `conflicting`,
   `uncovered-boundary`, `ambiguous`, or `runtime-unverified`. Include owner
   key, claim ID when applicable, expected behavior, implementation evidence,
   runtime status, and confidence for every finding.
7. Classify an external interaction not governed by the retrieved specification
   closure as `uncovered-boundary`. Its absence from a specification is not a
   conflict. Record whether every governing owner declares
   `coverage.external-boundary: exhaustive`.
8. Do not modify or delete anything.

Run a test only when it directly establishes a retrieved claim or verification
criterion. A concrete static call-path trace is sufficient to establish the
presence of an external interaction; do not run an unrelated runtime test or
lint merely to strengthen that classification.

## Report contract

Return these sections even when a section contains `none`:

1. Scope — retrieved owners and governing boundary coverage.
2. Claims checked — normative IDs and implementation-independent criteria.
3. Findings — classified entries with owner, claim, expectation, evidence,
   runtime status, and confidence.
4. Test evidence — exact focused checks and `passed`, `failed`,
   `environment-blocked`, or `not-run` status.
5. Verdict — conformance conclusion, remaining divergence, and confirmation
   that Verify changed no files.

When Verify surrounds an implementation, the final response must contain two
separate instances of this contract headed `Pre-change Verify` and
`Post-change Verify`, followed by an explicit list of finding transitions.
Reconstructing the pre-change state only as an informal retrospective summary
does not satisfy the contract.

Schema validity does not prove implementation conformance.
