# SpecSpine Adapter Generator

Repository-maintainer instructions. This file deliberately is not named
`SKILL.md`, so `npx skills` does not expose the generator as an installable
runtime skill.

Treat the publishable packages under `<repo-root>/skills/specspine-*` and
`<repo-root>/shared/references/` as the framework-neutral source of truth. This
tool owns shared-link validation and any framework-specific adapter generation.
Never put SDD framework knowledge into canonical runtime skills.

## Resources

- Read [references/generation-contract.md](references/generation-contract.md)
  before changing canonical skills, generated resources, or release behavior.
- Run `scripts/generate_resources.py --check` to validate shared-resource links.
- Run `scripts/generate_resources.py` to repair all shared-resource links.
  Use repeated `--skill <name>` only for focused iteration; run the full command
  before release.

## Workflow

1. Modify skill-specific files under `skills/`.
2. Keep all additional skill references canonical only in
   `shared/references/`.
3. Run `scripts/generate_resources.py` to repair links from runtime skills to
   shared references.
4. Run `scripts/generate_resources.py --check`.
5. Run skill validation, unit tests, the eval-manifest audit, and representative
   deterministic scripts.
6. Inspect the diff. Fix canonical shared resources and regenerate links; do
   not replace symlinks with skill-local copies.
7. Prepare publishing only after every gate passes. Publish through the
   repository's explicit release mechanism and only when the user authorizes
   the external action.

## Generation rules

- Keep additional instructions under `shared/` and expose them in each
  consuming skill through relative symbolic links.
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
- duplicate common references inside skill directories;
- make canonical runtime skills depend on a particular agent environment or SDD
  framework;
- use an LLM rewrite where deterministic byte copying is sufficient.
