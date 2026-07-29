---
name: specspine-extract
description: Use for read-only lookup and handoff from a configured SpecSpine when the user seeks architecture, durable requirements, contracts, reconstruction context, or specification documentation. Do not use for code-to-documentation mapping.
---

# SpecSpine Extract

Once loaded, do not reconsider or explain whether Extract was the correct
skill. Perform these steps only:

The bundled [vocabulary reference](references/spec-glossary.md) defines every
reserved identifier family, token, document kind, relation, and manifest value.
The retrieval script reads its machine source through `spec_contract.py`.

1. Resolve `<spine-root>` and documentation language from project instructions;
   default the root to `specspine`.
2. Build one compact query from the user request.
3. Invoke the bundled script exactly once:

```text
python3 <skill-root>/scripts/search_spine.py <spine-root> --query-json '<compact-json>'
```

4. Answer directly from the returned `task_context` and
   `concatenated_files`. `concatenated_source_paths` names the files already
   returned in full. If `concatenated_files_omitted_paths` is non-empty, read
   only those omitted files in one batched call when their full content is
   needed; never reread `concatenated_source_paths`. Do not inspect other
   project files or add unsupported conclusions.

## Query

Use paths relative to `<spine-root>`. Preserve exact paths, semantic IDs, API
names, and identifiers. Put synonyms for one concept in the same term group.
Write natural-language terms in the configured SpecSpine documentation language.
Do not generate translated or cross-language synonyms. Preserve a foreign-language
term only when it is an exact identifier, API name, or established term used by
the SpecSpine itself.

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

In the answer, cite returned paths as `<spine-root>/<returned-path>`. Preserve
the single status object, implementation freedom, aggregate and requested
facets, blockers, normative claims, registered assets, observations,
inferences, omissions, conflicts, evidence labels, and open questions. Treat
`OBS` and `INF` as orientation rather than requirements. Never upgrade
`incomplete` or `blocked` by inference and never claim code/spec conformance.
Use the user's requested format; otherwise return a concise direct answer.
