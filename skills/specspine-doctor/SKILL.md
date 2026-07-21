---
name: specspine-doctor
description: Diagnose and, when requested, repair mechanical integrity and semantic architecture health in an existing SpecSpine. Use when checking or fixing broken links, reachability, semantic IDs, evidence baselines, duplicate ownership, conflicting claims, poor decomposition, hidden uncertainty, implementation-detail leakage, handoff quality, or possible repository drift. It is self-contained and never guesses architectural intent.
---

# SpecSpine Doctor

Diagnose a SpecSpine, then repair findings when requested without reinterpreting
intent. Separate mechanical facts, semantic findings, and unconfirmed drift.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) and
  [references/spec-format.md](references/spec-format.md) before semantic
  diagnosis.
- Read [references/context-handoff.md](references/context-handoff.md) only when
  reviewing a handoff.
- Run `scripts/check_spine.py <spine-root>` for deterministic checks; use
  `--json` when structured results help.
- Read [references/review-method.md](references/review-method.md) before the
  semantic review or when classifying severity.

The script is an implementation aid, not the semantic authority. If its result
conflicts with the bundled rules, report the mismatch as a Doctor defect and
follow the references.

## Scope

Use one evidence mode:

- `spine-only` — default; inspect the full specification graph for internal
  integrity and semantic health;
- `repository-aware` — inspect representative project evidence to identify
  possible drift; require explicit user authorization unless the request
  already asks for comparison with the repository;
- `handoff` — review a supplied architecture context handoff against its source
  specifications.

Default to `check`, which is read-only. Use `repair` when the user asks to fix
findings. Diagnose before editing and remain self-contained.

## Workflow

### 1. Resolve rules and root

Load the bundled rules before classifying findings. Resolve `<spine-root>` from
the user request, applicable project instructions, existing integration, or
the documented default. Require its `README.md`.

### 2. Establish inspection boundary

State the selected mode and evidence boundary. In `spine-only`, do not inspect
project-specific material outside `<spine-root>`. In `repository-aware`, follow
the bundled repository-aware method and use the narrowest representative
evidence needed to evaluate suspected drift.

### 3. Run mechanical checks

Run the bundled checker. Independently verify any finding that may cause a
structural recommendation. Do not call a warning an error merely because a
project uses an optional section differently.

### 4. Review semantic health

Read `<spine-root>/README.md`, then traverse the complete reachable graph for a
whole-spine review. For a user-selected area, follow its direct neighborhood
and expand only when ownership or conflicts cross that boundary.

Apply `references/review-method.md`. Distinguish confirmed defects,
architecture risks, and questions requiring human judgment. Never convert
absence of information into a defect unless the bundled stopping rules require
that information.

### 5. Check drift when authorized

Compare intended claims with representative repository evidence. Record code
facts as observed and interpretations as inferred. Do not let implementation
evidence override decisions or constraints, and do not claim complete
conformance.

### 6. Repair when requested

Fix unambiguous mechanical defects directly, including balanced metadata
markers and uniquely resolvable links. Make broader structural or semantic
repairs only when meaning and canonical ownership are already clear. Ask for a
user decision before changing accepted intent not explicitly decided in the
current request, resolving a conflict or blocking question, choosing among
plausible owners, or deriving intent from repository evidence. Do not ask twice
when the current request already gives the decision. Modify only files under
`<spine-root>`, preserve unrelated content, then rerun affected checks. Report
anything left open.

### 7. Report

Report findings in severity order with stable local finding labels such as
`DOC-001`. These labels belong only to the report and must not be written into
SpecSpine documents.

For each finding include:

- severity and confidence;
- affected specification paths and semantic IDs when present;
- evidence or reasoning;
- impact;
- repair disposition: automatic, Doctor repair, or user decision required.

End with checked scope, unchecked scope, and a concise health summary. If no
defects are found, say only that no defects were found within the inspected
scope; do not certify conformance or completeness.

## Restrictions

Never:

- edit source code, integration artifacts, or other skills;
- edit specifications in `check` mode or outside `<spine-root>`;
- copy the bundled rules into the report;
- infer accepted intent from code or repetition;
- silently resolve ownership conflicts, accepted intent, or open questions;
- treat stylistic preference as a correctness error;
- claim formal validation, complete coverage, or code/spec conformance;
- require `specspine-init`, which is unrelated to specification semantics.
