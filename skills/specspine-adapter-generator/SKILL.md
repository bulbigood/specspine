---
name: specspine-adapter-generator
description: Maintain, regenerate, validate, and prepare the publishable specspine-init, specspine-grow, specspine-map, and specspine-doctor skill packages from one canonical build-time source. Use only for SpecSpine framework development, shared-rule updates, generated-package drift, release preparation, or package regeneration; ordinary project users do not need this skill installed.
---

# SpecSpine Adapter Generator

Maintain four autonomous runtime skills without runtime dependencies or
hand-edited duplicated rules. Treat files under `assets/skill-sources/` as
canonical and sibling `skills/specspine-{init,grow,map,doctor}/` directories as
generated output.

## Resources

- Read [references/generation-contract.md](references/generation-contract.md)
  before changing sources, generated packages, or release behavior.
- Run `scripts/generate_skills.py --check` to detect generated drift.
- Run `scripts/generate_skills.py` to regenerate all packages. Use repeated
  `--skill <name>` only for focused iteration; run the full command before
  release.

## Workflow

1. Modify only the canonical files under `assets/skill-sources/`.
2. Keep shared rules canonical in the `specspine-grow` source package. Generate
   the same `spec-format.md`, `spec-semantics.md`, and `context-handoff.md` into
   consumers that require them; never require runtime companion discovery.
3. Regenerate all four output packages.
4. Run `scripts/generate_skills.py --check`.
5. Run the repository's skill validation, unit tests, eval-manifest audit, and
   representative deterministic scripts.
6. Inspect the generated diff. Fix sources and regenerate; do not patch output.
7. Prepare publishing only after every gate passes. Publish through the
   repository's explicit release mechanism and only when the user authorizes
   the external action.

## Generation rules

- Keep published skills self-contained and independently installable.
- Put reusable executable logic in scripts so agents need not load it.
- Keep `SKILL.md` files concise and route conditional detail to references.
- Prefer build-time duplication over runtime skill dependencies.
- Do not generate project-specific architecture or SDD bindings here;
  `specspine-init` owns that one-time project adaptation.
- Do not include this maintainer skill in the generated package set.

## Restrictions

Never:

- edit generated runtime packages directly;
- publish when generation check, validation, or tests fail;
- publish without explicit authorization;
- make runtime skills depend on this generator;
- treat generated manifests as project architecture;
- use an LLM rewrite where deterministic byte copying is sufficient.
