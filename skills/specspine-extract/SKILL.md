---
name: specspine-extract
description: Retrieve a task-bounded specification closure from a Specspine v5 IWE library. Use when implementation work needs accepted contracts, constraints, evidence, or verification criteria.
---

# Specspine Extract

Use IWE as the only retrieval engine.

1. Find seeds with `iwe find --fuzzy`, `--lexical`, or frontmatter filters.
2. Retrieve a bounded closure:

   ```bash
   iwe retrieve -k <key> --expand-includes 1 --expand-included-by 1 \
     --expand-references 1 --children --backlinks
   ```

3. Increase depths only when the task requires additional context. Use token
   and document limits for agent-facing output.
4. Report normative statements separately from `OBS`, `INF`, and `OQ`.

Do not parse Markdown links, build a private index, or search `_INDEX.md`.
