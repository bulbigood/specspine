# Retrieval corpus contract

Each corpus is immutable benchmark input with this layout:

```text
<corpus-id>/
├── manifest.json
└── project/
    ├── AGENTS.md
    └── specspine/
        ├── README.md
        └── ...
```

`manifest.json` follows [manifest.schema.json](manifest.schema.json).
`documents` is the exact SHA-256 inventory of Markdown files below
`project/specspine`, relative to that directory.

Every scenario contains both:

- a natural user request for agent-level Extract evaluation;
- fixed structured slices for ranker-only A/B evaluation.

Judgment grades are:

- `3`: the single canonical owner for the slice;
- `2`: required supporting context;
- `1`: acceptable but optional context;
- `0`: an explicitly labeled hard negative.

Unlisted documents are ordinary irrelevant documents. A grade-3 owner in a
ranking scenario must be a direct result. Model distributed ownership as
multiple slices, not multiple grade-3 documents in one slice.

Use `evaluation: ranking` for cases that compare ordered retrieval results.
Use `evaluation: protocol` for `no_match`, malformed-input, output-budget, and
other cases whose expected behavior is not a ranking metric.

Do not encode expected numeric scores or timings. Do not make normal scenarios
trivial with generated unique tokens. Reserve exact paths, titles, and semantic
IDs for scenarios explicitly tagged as exact-match coverage.

Validate a corpus with:

```text
python3 tools/specspine-extract/validate_corpus.py <corpus>/manifest.json
```
