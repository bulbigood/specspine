---
name: specspine-connect
description: Connect an existing SpecSpine to persistent project-agent instructions. Use to install, refresh, repair, configure retrieval acceleration, or remove the small managed discovery bootstrap. Does not create a SpecSpine or adapt downstream frameworks.
---

# SpecSpine Connect

Install one small, framework-neutral retrieval block in the project's persistent
agent instructions. It records the index, documentation language, and retrieval
accelerator policy; routes architecture-relevant work through
`specspine-extract`; and preserves linked Markdown navigation as fallback.

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
4. Resolve retrieval acceleration from an explicit request, then a recognized
   existing `auto` or `disabled` policy, otherwise `auto`. Preserve existing
   policy on refresh. Ask before repairing an unrecognized value. Never infer
   policy from the current runtime environment.
5. On install, refresh, repair, or configuration, add or replace exactly one
   balanced `specspine:begin` / `specspine:end` block. Preserve all content
   outside it. An explicit request authorizes the edit when the target path is
   unambiguous.
6. Verify the index path, documentation language, accelerator policy, balanced
   unique markers, lack of unresolved `{{...}}` placeholders, preservation of
   surrounding content, and idempotency.
7. Report the changed file and resolved configuration. Mention unresolved
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
