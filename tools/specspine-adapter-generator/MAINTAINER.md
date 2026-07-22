# SpecSpine Adapter Generator

Repository-maintainer instructions. This file deliberately is not named
`SKILL.md`, so `npx skills` does not expose the generator as an installable
runtime skill.

Treat the publishable packages under `<repo-root>/skills/specspine-*` as the
framework-neutral source of truth. This tool owns both shared-resource
synchronization and any framework-specific adapter generation. Never put SDD
framework knowledge into canonical runtime skills.

## Resources

- Read [references/generation-contract.md](references/generation-contract.md)
  before changing canonical skills, generated resources, or release behavior.
- Run `scripts/generate_resources.py --check` to detect shared-resource drift.
- Run `scripts/generate_resources.py` to synchronize all derived resources.
  Use repeated `--skill <name>` only for focused iteration; run the full command
  before release.

## Workflow

1. Modify canonical files only under `skills/`.
2. Keep shared rules canonical in `skills/specspine-grow/references/`.
3. Run `scripts/generate_resources.py` to synchronize shared specification
   rules into `specspine-map` and `specspine-doctor`.
4. Run `scripts/generate_resources.py --check`.
5. Run skill validation, unit tests, the eval-manifest audit, and representative
   deterministic scripts.
6. Inspect the diff. Fix canonical owner resources and regenerate; do not patch
   shared consumer copies.
7. Prepare publishing only after every gate passes. Publish through the
   repository's explicit release mechanism and only when the user authorizes
   the external action.

## Generation rules

- Keep published skills self-contained and independently installable.
- Put reusable executable logic in skill `scripts/` directories.
- Keep `SKILL.md` files concise and route conditional detail to references.
- Prefer build-time shared copies over runtime skill dependencies.
- Keep framework-specific commands, artifact layouts, lifecycle stages,
  templates, and compatibility rules in adapters generated from this tool.
- Build adapters against the neutral context handoff and agent-bootstrap
  contracts; do not patch canonical skills for a framework.
- Do not generate project-specific architecture or configuration bindings.

## Restrictions

Never:

- store skill snapshots or copied skill sources under `tools/`;
- publish when generation check, validation, or tests fail;
- publish without explicit authorization;
- make runtime skills depend on this generator;
- make canonical runtime skills depend on a particular agent environment or SDD
  framework;
- use an LLM rewrite where deterministic byte copying is sufficient.
