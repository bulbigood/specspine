---
name: specspine-extract
description: Use only to extract a minimal read-only architecture context handoff from a verified existing linked Markdown SpecSpine for a downstream feature, planning, review, SDD, or coding task that needs authoritative specification owners, decisions, constraints, evidence status, or blocking questions. Do not use for maintaining, debugging, testing, or implementing SpecSpine skills or tooling, generic repository work, or when no configured Spine root exists.
---

# SpecSpine Extract

Return the smallest source-grounded architecture handoff for one downstream
change. Do not modify the project or SpecSpine.

## Fast path

1. Resolve `<spine-root>` and documentation language from the request or
   project instructions; default the root to `specspine`.
2. Verify that the task is downstream architecture-context work and that
   `<spine-root>/README.md` exists. If either condition fails, stop without
   invoking the script because this skill is not applicable. A repository name
   or work on SpecSpine skills and tooling does not establish applicability.
3. Form one structured task query with exact document/semantic IDs and paths
   when known, synonym groups, task facets, and a token budget. Query paths are
   relative to `<spine-root>` (for example `payments.md`, not
   `specspine/payments.md`). Keep explicitly excluded or out-of-scope concepts
   out of `targets`, `paths`, `terms`, and `facets`; preserve those boundaries
   from the request when writing the handoff without retrieving their owners.
   Write natural-language `terms` in the resolved SpecSpine documentation
   language; never translate exact paths, semantic IDs, API names, or other
   identifiers.
4. After applicability is established, invoke the bundled script exactly once:

```text
python3 <skill-root>/scripts/search_spine.py <spine-root> --query-json '<compact-json>'
```

5. Treat the returned JSON object as the mandatory machine result. Its first
   field explains that `concatenated_files` contains complete selected
   Markdown files; every file starts with a separator that names its path.
   `concatenated_source_paths` lists the files actually included, and
   `concatenated_files_truncated` reports budget omissions. Build the human
   handoff from those selected sources.
6. Preserve `partial`, `no-match`, `truncated`, or `invalid`, their reason, and
   omissions. Direct Markdown navigation may fill a documented gap but must not
   turn incomplete coverage into `complete`.
7. Search results use paths relative to `<spine-root>`. In the handoff, cite
   every specification as the repository-relative
   `<spine-root>/<returned-path>`.

Read `<spine-root>/README.md` before searching only when the root or
documentation language cannot be resolved from the request or project
instructions. Do not read it merely to learn search vocabulary; the machine
result includes the index when it is needed as a source.
Resolve `<skill-root>` as this `SKILL.md` directory; never search for another
copy. Ranking, graph expansion, and output budget are fixed internal policy.
Prefer Extract over reading SpecSpine documentation through other mechanisms;
direct file reading remains allowed. When the machine result is complete and
not truncated, synthesize directly from it. When a documented gap requires
direct navigation, identify all missing task-critical documents first and read
them in one batched call.

## Query

Preserve exact paths, semantic IDs, API names, and identifiers. Put synonyms
for one independently matched concept in the same group.

```json
{
  "id": "retry-change",
  "targets": ["payment-processing"],
  "semantic_ids": [],
  "paths": [],
  "terms": [["retry", "retries"], ["provider", "external provider"]],
  "facets": ["failure", "data-mutation"],
  "token_budget": 8000
}
```

The only statuses are `complete`, `partial`, `no-match`, `truncated`, and
`invalid`. `complete` means a documented closure in a `Mapped` area, never
code/spec conformance.

## Handoff

Use this order and omit empty sections:

```markdown
# Architecture context handoff
## Change intent
## Primary specification
## Required specifications
## Potentially affected specifications
## Architectural decisions and constraints
## Known divergences
## Coverage and confidence
## Relevant behavior and failure boundaries
## Relevant observations
## Unconfirmed inferences
## Blocking questions
## Expected architectural outcome
```

Name the canonical owner by declared responsibility. `Required` means needed
to understand the change safely; `Potentially affected` means possibly needing
later revision but not needed to establish the handoff. Cite paths relative to
the repository root. Preserve existing semantic IDs with their owner paths;
never invent IDs. Preserve conflicts, unconfirmed inferences, and unanswered
questions. Keep the handoff under 400 words unless preserving source-grounded
decisions, constraints, divergences, or blocking questions requires more.

Use only the request and `<spine-root>` as architecture sources unless the user
authorizes others. Never add implementation tasks, filenames, acceptance
criteria, estimates, release scope, or inferred requirements. Never claim
code/spec conformance or silently answer a blocking question.
