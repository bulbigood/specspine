---
name: specspine-verify
description: Verify an implementation or blind reconstruction against a configured SpecSpine's normative claims, owned contracts, readiness, and conformance assets. Use for code/spec conformance assessment and reconstruction benchmarks. Do not use to create intent, map architecture, or silently repair code or specifications.
---

# SpecSpine Verify

Verification is read-only unless the user separately requests a repair. It
reports evidence; it never creates accepted intent or changes readiness.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) completely
  before classifying conformance.
- Read [references/spec-format.md](references/spec-format.md) for normative
  claims, assets, readiness, and blocking questions.
- Resolve configured presentation headings to canonical v3 keys before
  evaluating coverage or conformance.
- Run `scripts/check_spine.py <spine-root>` before verification.
- Use installed `specspine-extract` once to obtain the smallest applicable
  normative closure. If unavailable, navigate from the index without expanding
  beyond the requested scope.

## Workflow

1. Resolve `<spine-root>` and require its `_INDEX.md`.
2. Run the mechanical checker. Stop on errors that make the selected closure
   invalid.
3. Resolve implementation freedom, the primary owner, normative claims, owned
   contracts, verification assets, known divergences, and blocking questions.
4. Select only implementation evidence needed for the requested scope: public
   surfaces, configuration, tests, build results, or runtime observations.
5. Run owned conformance checks when safe and authorized. Treat their output as
   verification evidence, not normative authority.
6. Classify each applicable normative claim as:
   - `verified` — direct evidence satisfies it;
   - `violated` — direct evidence contradicts it;
   - `not-exercised` — no sufficient check was run;
   - `blocked` — required policy or evidence is unavailable.
7. Report claim IDs, owner paths, evidence, limitations, and aggregate result.

## Blind reconstruction

For a blind benchmark, use a new isolated workspace and provide the producer
only the selected SpecSpine closure, owned assets, and standard toolchains.
Never inspect or copy original implementation source. Evaluate the result with
an independently held conformance suite. Record every policy the producer had
to invent as a specification gap.

## Boundaries

- Never infer a requirement from `OBS`, code, tests, or runtime repetition.
- Evaluate only the equivalence promised by `implementation_freedom`; do not
  require source or internal similarity from a contract-equivalent result.
- Never change manifest facets or blockers; Evolve owns accepted specification
  changes.
- Never claim untested statements are verified.
- Never modify implementation or SpecSpine without a separate explicit request.
- A passing suite proves only the claims it exercises, not total conformance.
