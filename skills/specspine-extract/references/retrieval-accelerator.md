# Retrieval accelerator

`scripts/search_spine.py` derives a local SQLite FTS5 index and link graph from
the Markdown files under `<spine-root>`. The Markdown network remains the only
architecture source; the index is disposable routing data.

Unless the request or environment explicitly prevents execution, run this once
before any content search beyond `README.md`:

```text
python3 <skill-root>/scripts/search_spine.py <spine-root> --query <change-intent>
```

Do not replace this first attempt with repository-wide `rg`, `grep`, or manual
document scanning. Use those only after the command returns fallback or cannot
be executed.

Exit `0` returns JSON candidates. Read the current Markdown index, candidate
documents, and justified linked neighbors before extracting any claims. Cached
summaries and scores select sources; they are not handoff evidence. Candidate
paths are relative to `<spine-root>`; render handoff addresses using the
repository-root-relative form required by the handoff contract.

Exit `2`, an empty candidate list, malformed output, or any inability to run the
command means the accelerator is unavailable. Continue from `README.md` through
ordinary Markdown links without treating this as a SpecSpine defect. The
accelerator must never block extraction.

The script uses only Python's standard library, checks FTS5 directly, refreshes
changed files before search, and stores its cache outside `<spine-root>`. Set
`SPECSPINE_CACHE_DIR` only when a different disposable cache location is useful.
The cache may be deleted at any time.
