---
name: specspine-extract-v2
description: Produce a minimal task-oriented architecture context handoff from an existing linked Markdown SpecSpine using one benchmark-only batched retrieval call. Use only when a repeatable evaluation explicitly stages this v2 skill to measure semantic query decomposition, legacy versus faceted BM25 retrieval, returned-document cost, canonical-owner discovery, and downstream handoff quality without changing the persistent SpecSpine.
---

# SpecSpine Extract V2

Create a temporary projection of the persistent SpecSpine for one downstream
change. This benchmark-only variant exercises structured batched retrieval and
must not modify the SpecSpine.

## Workflow

1. Resolve `<spine-root>` from the request, project instructions, or the
   documented default `specspine`. Require `<spine-root>/README.md`.
2. Read [references/context-handoff.md](references/context-handoff.md) and
   `<spine-root>/README.md`. Use the index to understand system boundaries and
   establish the change intent without inventing requirements.
3. Identify every independently owned architectural target needed to understand
   the request. Create one slice per target and collect all slices before
   searching.
4. Run the bundled accelerator exactly once. Consume its marked document blocks
   directly; do not issue separate reads for documents whose complete content
   was returned.
5. Use returned direct documents and only graph documents whose relationship
   justifies their inclusion. If a required hit is marked `DOCUMENT_OMITTED`,
   read that file normally. On fallback, malformed output, or required
   `no_match`, do not retry the accelerator; navigate from the already-read
   index through ordinary Markdown links.
6. Verify the canonical owner and every relied-on semantic ID against complete
   source text from the index, returned document blocks, or explicit reads.
7. Render the smallest useful handoff using the bundled contract. Return it in
   the response unless the user explicitly requested a file outside the
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
document; do not encode every concept from the user request as one target.
Preserve exact paths, semantic IDs, API names, and identifiers. Write
descriptive terms in the configured documentation language.

Run:

```text
python3 <skill-root>/scripts/search_spine_v2.py <spine-root> --ranking "${SPECSPINE_EXTRACT_V2_RANKING:-faceted-bm25}" --queries-json '<compact-json>'
```

Resolve `<skill-root>` as the directory containing this `SKILL.md`. Never
discover or substitute another copy. The environment-controlled ranking value
is part of the benchmark arm; do not override it or run both strategies.

Interpret the protocol as follows:

- `SLICE status=matched` means at least one strict direct match was found.
- `SLICE status=no_match` means the strict description produced no direct
  owner; use index navigation without another accelerator call.
- `HIT origin=direct` identifies independently ranked candidates.
- `HIT origin=graph` identifies linked context and is not automatically
  required.
- `DOCUMENT` contains current complete Markdown source and may support evidence.
- `DOCUMENT_OMITTED` contains no source text and requires an explicit read when
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
acceptance criteria, tasks, ordering, implementation filenames, test
scenarios, estimates, release scope, or implementation status. Never silently
answer blocking questions, promote inference, claim code/spec conformance, or
treat extraction readiness as implementation readiness.
