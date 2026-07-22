---
name: specspine-doctor
description: Check reproducible mechanical integrity and perform advisory semantic review of an existing SpecSpine. Use for broken links, reachability, semantic IDs, evidence baselines, duplicate ownership risks, conflicting claims, poor decomposition, hidden uncertainty, implementation-detail leakage, or handoff quality. Use specspine-map for repository drift analysis. Doctor may invoke specspine-extract when diagnosing or repairing a handoff and otherwise never guesses architectural intent.
---

# SpecSpine Doctor

Runtime contract: SpecSpine v1. If another installed SpecSpine skill reports a
different contract version, report version skew before suggesting repairs.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before an
  advisory semantic review.
- Read [references/spec-format.md](references/spec-format.md) only when a
  finding or repair depends on document organization, addressable-statement
  syntax, or stopping rules.
- For a handoff pass, invoke `specspine-extract` and use its contract; do not
  duplicate that protocol here.
- Run `scripts/check_spine.py <spine-root>` for deterministic checks; use
  `--json` when structured results help.
- Read [references/review-method.md](references/review-method.md) before the
  semantic review or when classifying severity.

The script owns only reproducible mechanical findings. The semantic references
guide an advisory, necessarily incomplete review; they do not define a solver
or validation algorithm.

## Scope

Use one evidence mode:

- `spine-only` — default; inspect the full specification graph for mechanical
  integrity and advisory architectural risks;
- `handoff` — invoke `specspine-extract`, then review the handoff against its
  source specifications.

Default to `check`, which is read-only. Use `repair` when the user asks to fix
findings. Diagnose before editing and remain self-contained.

## Workflow

### 1. Resolve rules and root

Load only the bundled rules required by the selected pass before classifying
findings. Resolve `<spine-root>` from the user request, applicable project
instructions, existing integration, or the documented default. Require its
`README.md`.

### 2. Establish inspection boundary

State the selected mode and evidence boundary. Do not inspect project-specific
material outside `<spine-root>`; route repository drift analysis to
`specspine-map`.

### 3. Run mechanical checks

Run the bundled checker. Independently verify any finding that may cause a
structural recommendation. Do not call a warning an error merely because a
project uses an optional section differently.

### 4. Perform advisory semantic review

Read `<spine-root>/README.md`, then traverse the complete reachable graph for a
whole-spine review. For a user-selected area, follow its direct neighborhood
and expand only when ownership or conflicts cross that boundary.

Apply `references/review-method.md`. Report evidence-backed architectural risks
with confidence, not semantic pass/fail results. Never claim that the review is
complete or that absence of a finding establishes validity. Never convert
absence of information into a finding unless the bundled stopping rules make
it relevant to the document's stated purpose.

### 5. Repair when requested

Fix unambiguous mechanical defects directly, including balanced metadata
markers and uniquely resolvable links. Make broader structural or semantic
repairs only when meaning and canonical ownership are already clear. Ask for a
user decision before changing accepted intent not explicitly decided in the
current request, resolving a conflict or blocking question, choosing among
plausible owners, or deriving intent from repository evidence. Do not ask twice
when the current request already gives the decision. Modify only files under
`<spine-root>`, preserve unrelated content, then rerun affected checks. Report
anything left open.

### 6. Report

Report two independent channels. Start with `Mechanical integrity: PASS` or
`Mechanical integrity: FAIL`, then list checker findings using code, severity,
path, line, and message. Mechanical status must depend only on reproducible
checker errors.

Under `Advisory semantic findings`, give review findings stable report-local
labels such as `DOC-001`. Include confidence, affected paths and IDs, evidence
or reasoning, impact, and repair disposition when useful. Advisory findings do
not change mechanical PASS/FAIL. Never write report labels into SpecSpine
documents.

End with checked scope, unchecked scope, mechanical status, and review
limitations. If no findings remain, say only that none were found within the
inspected scope; do not certify semantic validity, conformance, or completeness.

## Restrictions

Never:

- edit source code, integration artifacts, or other skills;
- edit specifications in `check` mode or outside `<spine-root>`;
- copy the bundled rules into the report;
- infer accepted intent from code or repetition;
- silently resolve ownership conflicts, accepted intent, or open questions;
- treat stylistic preference as a correctness error;
- claim semantic validity, formal validation, complete review coverage, or
  code/spec conformance;
- require `specspine-connect`, which is unrelated to specification semantics.
