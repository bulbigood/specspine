---
name: specspine-connect
description: Connect an existing SpecSpine to persistent project-agent instructions. Use to install, refresh, repair, or remove the small managed discovery bootstrap. Does not create a SpecSpine or adapt downstream frameworks.
---

# SpecSpine Connect

Install one small, framework-neutral retrieval block in the project's persistent
agent instructions. The block routes architecture-relevant downstream work
through `specspine-extract` when installed and preserves linked Markdown
navigation as fallback, without copying architecture or prescribing a
downstream workflow.

## Resources

- Read [references/bootstrap-contract.md](references/bootstrap-contract.md)
  before changing the bootstrap.
- Render [assets/templates/agent-bootstrap.md](assets/templates/agent-bootstrap.md)
  into the selected persistent instruction file.

## Boundaries

Own only the text between the managed markers. Do not edit specifications,
source code, tests, downstream artifacts, skills, or global agent
configuration.

Inspect only the SpecSpine index, applicable persistent project instructions,
and an existing managed block. Do not inspect implementation or discover and
adapt SDD frameworks, tools, commands, templates, paths, or conventions.

## Workflow

1. Resolve `<spine-root>` from the user, applicable project instructions, an
   existing managed block, or the default `specspine`, in that order. Require
   `<spine-root>/README.md`; do not create it.
2. Select the applicable persistent project-agent instruction file, such as
   `AGENTS.md`, using existing project rules and the user request. If several
   surfaces are equally plausible, ask which one to use.
3. Resolve the SpecSpine documentation language from an existing managed block,
   the request, applicable project instructions, or the index. Ask only when
   those sources remain ambiguous.
4. On install, refresh, or repair, add or replace exactly one balanced
   `specspine:begin` / `specspine:end` block. Preserve all content outside it.
   An explicit request authorizes the edit when the target path is unambiguous.
5. Verify the index path, documentation language, balanced unique markers, lack
   of unresolved `{{...}}` placeholders, preservation of surrounding content,
   and idempotency.
6. Report the changed file and resolved index and language. Mention unresolved
   choices only when they prevent a safe edit.

## Refresh and removal

Refresh by replacing only the managed block. On explicit removal, remove only
that block. Never delete a user-owned instruction file merely because it
becomes empty.

## Restrictions

Never:

- generate a binding, adapter, or project-local or global skill;
- add framework-specific instructions to the bootstrap;
- make downstream artifacts architectural authority;
- treat observations or inferences as accepted intent;
- resolve SpecSpine conflicts or open questions;
- claim framework compatibility or code/spec conformance.
