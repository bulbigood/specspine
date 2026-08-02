---
name: iwe-spec-implement
description: Bring an implementation into conformance with accepted Specspine v5 specifications retrieved through IWE using additive, conform, or closed-boundary reconciliation. Use when an operator asks to implement specified behavior, fix code/spec divergence, satisfy verification criteria, remove conflicting behavior, or prune unspecified external integrations from an explicitly exhaustive boundary.
---

# IWE Spec Implement

Change implementation, tests, and implementation-owned configuration. Do not
change accepted specifications to make the implementation pass. Use `conform`
unless the operator selects another mode.

Use the official `iwe-memory-system` skill for all IWE operations. If it is not
available, obtain it from the official `iwe-org/skills` distribution through
the environment's supported skill-installation mechanism. Read it before
continuing. Do not substitute generic CLI help or guess syntax that the skill
or targeted command help can establish. Also use the `iwe-spec-verify` skill;
Verify is a report procedure, not an IWE subcommand.

Inspect `.iwe/config.toml` before starting. Read the
[IWE bootstrap protocol](references/iwe-bootstrap.md) only when IWE is not
initialized, its Specspine template or schema is missing, or the requested
library path conflicts with the configured path.

## Modes

- `additive`: implement `missing` claims. Report all other findings without
  removing behavior.
- `conform` (default): implement `missing` claims and resolve `conflicting`
  behavior that has a concrete normative basis.
- `closed-boundary`: do everything in `conform`, then remove
  `uncovered-boundary` behavior only when every owner governing that behavior
  declares `coverage.external-boundary: exhaustive`.

1. Resolve the operator's terms to specification owners with `iwe find`. If
   several owners plausibly match, inspect their titles and neighborhoods
   before choosing.
2. Run `iwe schema validate`; stop on schema errors.
3. Retrieve a task-bounded closure with `iwe retrieve`, expanding inclusion,
   references, children, and backlinks only as far as the task requires.
4. Produce the complete pre-change report required by `iwe-spec-verify`.
   Classify findings as `conforming`, `missing`, `conflicting`,
   `uncovered-boundary`, `ambiguous`, or `runtime-unverified`. Treat `REQ`,
   `GUA`, `INV`, `QLT`, `DEC`, `CON`, and `VER` as normative; treat `OBS` and
   `INF` only as evidence.
   Capture every required report field before editing and reproduce this report
   under `Pre-change Verify` in the final response.
5. Trace each relevant normative claim to code, tests, and registered assets.
   Record every applicable Verify finding class, using explicit `none` for
   classes without findings, before editing.
6. Apply only the finding classes authorized by the selected mode. Implement
   the smallest coherent change that resolves them. Preserve unrelated
   behavior and follow repository conventions.
7. Add or update focused tests that demonstrate the normative behavior. Run
   the smallest relevant test. Run a broader suite only after the focused test
   passes and only when the change's risk justifies it. Follow the shared
   environment-blocked stop rule.
8. Run `iwe schema validate` once after the implementation and produce the
   complete post-change `iwe-spec-verify` report over the same scope. Report
   changed files, before/after finding transitions, satisfied claims, remaining
   divergence, and runtime-unverified claims.
   The exact final headings are `Pre-change Verify`; `Post-change Verify`;
   `Finding transitions`. Include all five Verify report sections under each
   Verify heading, including explicit `none` values.

## Removal policy

Remove behavior only when evidence establishes that it conflicts with accepted
intent. A feature is removable when at least one of these holds:

- a normative claim explicitly forbids it;
- it violates an invariant, constraint, guarantee, or decision;
- the specification defines an exhaustive behavior boundary that excludes it;
- keeping it makes a verification criterion fail.

Do not infer prohibition from silence. If behavior is merely undocumented,
report it as unverified instead of deleting it. Before deletion, inspect callers,
public interfaces, data migrations, configuration, and tests. Remove the full
now-dead path only when doing so is safe and within the operator's scope.
After a deletion or block removal, inspect the immediate splice boundaries for
duplicated comments, annotations, declarations, or malformed structure before
running checks.

Treat network calls, public APIs, queues, events, files, databases, external
storage, email, messaging, child processes, and telemetry as external-boundary
behavior. Classify an unmentioned external interaction as
`uncovered-boundary`, not `conflicting`. In `closed-boundary` mode, absence is
actionable only under explicit exhaustive coverage; otherwise report it and
preserve it.

## Guardrails

- Stop rather than guess when a relevant blocking `OQ-*` leaves the intended
  behavior materially ambiguous.
- Do not rewrite normative claims, weaken verification criteria, or relabel
  implementation evidence as accepted intent. Use `iwe-spec-specify` only when
  the operator explicitly asks to change the specification.
- A passing schema validates documents, not implementation conformance.
- A passing test suite is supporting evidence, not permission to ignore an
  uncovered normative claim.
