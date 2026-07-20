---
name: specspine-doctor
description: Diagnose mechanical integrity and semantic architecture health in an existing SpecSpine. Use when checking broken links, reachability, semantic IDs, duplicate ownership, conflicting claims, poor decomposition, hidden uncertainty, implementation-detail leakage, handoff quality, or possible repository drift. This skill is read-only and requires an installed specspine-grow or specspine-map companion for the current SpecSpine rules.
---

# SpecSpine Doctor

Diagnose a SpecSpine without silently repairing or reinterpreting it. Report
mechanical facts separately from semantic findings and unconfirmed drift.

## Required companion

Do not duplicate or reconstruct the SpecSpine format and claim semantics.
Before diagnosis, locate an installed companion through the active skill
catalog:

- for a spine-only review, prefer `specspine-grow`; if unavailable, use
  `specspine-map`;
- for a repository-aware drift review, require `specspine-map`.

Read the selected companion's complete `SKILL.md`, then its
`references/spec-semantics.md` and `references/spec-format.md`. Treat those
files as the current rules. Read `references/context-handoff.md` only when
reviewing a handoff.

If no suitable companion is installed or its resources cannot be read, stop
and report the missing prerequisite. Do not fall back to remembered rules.

## Resources

- Run `scripts/check_spine.py <spine-root>` for deterministic checks. It emits
  human-readable findings and exits nonzero when errors exist. Use `--json`
  when structured results help.
- Read [references/review-method.md](references/review-method.md) before the
  semantic review or when classifying severity.

The script is an implementation aid, not the semantic authority. If its result
conflicts with the companion rules, report the mismatch as a Doctor defect and
follow the companion rules.

## Scope

Use one explicit mode:

- `spine-only` — default; inspect the full specification graph for internal
  integrity and semantic health;
- `repository-aware` — inspect representative project evidence to identify
  possible drift; require explicit user authorization unless the request
  already asks for comparison with the repository;
- `handoff` — review a supplied architecture context handoff against its source
  specifications.

Remain read-only in every mode. When the user asks to fix findings, finish the
diagnosis first and route normative changes through `specspine-grow` and
repository-evidence changes through `specspine-map`. Do not create an
independent repair workflow.

## Workflow

### 1. Resolve rules and root

Load the companion rules before classifying findings. Resolve `<spine-root>`
from the user request, applicable project instructions, existing integration,
or the companion's documented default. Require its `README.md`.

### 2. Establish inspection boundary

State the selected mode and evidence boundary. In `spine-only`, do not inspect
project-specific material outside `<spine-root>`. In `repository-aware`, follow
the mapping skill's evidence discipline and use the narrowest representative
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
absence of information into a defect unless the companion's stopping rules
require that information.

### 5. Check drift when authorized

Compare intended claims with representative repository evidence. Record code
facts as observed and interpretations as inferred. Do not let implementation
evidence override decisions or constraints, and do not claim complete
conformance.

### 6. Report

Report findings in severity order with stable local finding labels such as
`DOC-001`. These labels belong only to the report and must not be written into
SpecSpine documents.

For each finding include:

- severity and confidence;
- affected specification paths and semantic IDs when present;
- evidence or reasoning;
- impact;
- recommended owner: Doctor script, `specspine-grow`, `specspine-map`, or user
  decision.

End with checked scope, unchecked scope, and a concise health summary. If no
defects are found, say only that no defects were found within the inspected
scope; do not certify conformance or completeness.

## Restrictions

Never:

- edit specifications, source code, integration artifacts, or companion skills;
- copy the companion rules into this skill or the report;
- infer accepted intent from code or repetition;
- silently resolve ownership conflicts or open questions;
- treat stylistic preference as a correctness error;
- claim formal validation, complete coverage, or code/spec conformance;
- require `specspine-init`, which is unrelated to specification semantics.
