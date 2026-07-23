---
name: specspine-extract
description: Extract a minimal task-oriented architecture context handoff from an existing linked Markdown SpecSpine. Use when downstream feature, SDD, planning, review, or coding work needs authoritative owners, affected specifications, preserved decisions and constraints, evidence status, or blocking questions without modifying the persistent SpecSpine.
---

# SpecSpine Extract

Create a temporary projection of the persistent SpecSpine for one downstream
change.

## Workflow

1. Resolve `<spine-root>` from the request, project instructions, or the
   documented default `specspine`. Require `<spine-root>/README.md`.
2. Read [references/context-handoff.md](references/context-handoff.md) and
   `<spine-root>/README.md`. Use the index to establish system boundaries and
   the change intent without inventing requirements.
3. Identify every independently owned architectural target needed to understand
   the request. Create one query slice per target and collect all slices before
   searching.
4. Unless project instructions disable the retrieval accelerator, run the
   bundled script exactly once. Consume its marked document blocks directly;
   never reread complete returned documents.
5. Use direct documents and only graph documents whose relationship is relevant
   to the change. If a necessary hit is marked `DOCUMENT_OMITTED`, read that
   file normally. On unavailable execution, fallback, malformed output, or a
   necessary `no_match`, do not retry the script; navigate from the already-read
   index through ordinary Markdown links.
6. Verify the canonical owner and every relied-on semantic ID against complete
   source text from the index, returned document blocks, or explicit reads.
7. Render the smallest useful handoff using the bundled contract. Return it in
   the response unless the user explicitly requests a file outside the
   persistent SpecSpine.

## Structured retrieval

Describe each target with two to four independent lexical features:

```json
[
  {
    "id": "retry-owner",
    "must": [
      ["retry", "retries"],
      ["provider", "external provider"],
      ["timeout", "timed-out"]
    ],
    "should": [
      ["backoff"],
      ["attempt"]
    ]
  },
  {
    "id": "rate-limit-owner",
    "must": [
      ["rate limit", "rate-limit", "throttling"],
      ["provider", "external provider"]
    ]
  }
]
```

Inside one group, include only lexical alternatives for the same feature.
Place related but non-equivalent concepts in separate `should` groups. A
`must` feature must be highly likely to occur literally in the canonical
document; do not encode every concept from the request as one target. Preserve
exact paths, semantic IDs, API names, and identifiers. Write descriptive terms
in the configured documentation language.

Run:

```text
python3 <skill-root>/scripts/search_spine.py <spine-root> --queries-json '<compact-json>'
```

Resolve `<skill-root>` as the directory containing this `SKILL.md`. Never
discover or substitute another copy. Ranking, graph traversal, and output
budget are internal policy; do not add tuning arguments.

Interpret the protocol:

- `SLICE status=matched` means at least one strict or normalized direct match.
- `SLICE status=no_match` means the slice found no direct owner.
- `HIT origin=direct` identifies independently ranked candidates.
- `HIT origin=graph` identifies linked context and is not automatically
  required.
- `DOCUMENT` contains complete current Markdown source.
- `DOCUMENT_OMITTED` contains no source and requires an explicit read only when
  the hit is necessary.
- `truncated=true` means at least one selected document was omitted.

## Source boundary

Use only the current request and files inside `<spine-root>` as architecture
sources. Inspect project code, configuration, tests, other documentation,
tools, or external systems only when the user explicitly authorizes them.
Authorized external evidence remains `Observed` or `Inferred` unless separately
accepted as intent.

## Restrictions

Never modify the SpecSpine, implementation, or downstream artifacts while
extracting. A disposable cache outside `<spine-root>` is allowed. Never add
acceptance criteria, tasks, ordering, implementation filenames, test scenarios,
estimates, release scope, or implementation status. Never silently answer
blocking questions, promote inference, claim code/spec conformance, or treat
extraction readiness as implementation readiness.
