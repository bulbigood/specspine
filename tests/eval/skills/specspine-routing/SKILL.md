---
name: specspine-routing
description: Evaluation-only entrypoint for testing skill selection from installed companion metadata.
---

# SpecSpine routing evaluation

Before acting, read only the YAML frontmatter of each installed companion
`SKILL.md`. Select a companion solely from its `description`.

- If one description matches, read that companion's complete `SKILL.md` and
  follow it.
- If none matches, do the user request directly without reading any companion
  beyond its frontmatter.

Do not invoke a companion merely to ask it whether it applies.
