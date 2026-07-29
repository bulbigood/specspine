# SpecSpine Map topic-review contract

Review the complete compact semantic mapping in a fresh isolated context.
Compare descriptions and source provenance, never ID spelling or source-tree
shape. Correct residual duplicates, accidental mega-topics, mixed ownership,
framework categories, unsupported coverage, and source topics incorrectly
classified as supporting.

Re-evaluate every canonical topic against existing SpecSpine owners and exact
claims. Zero covered topics is suspicious whenever non-index documents exist:
accept it only after checking every candidate owner. Prefer one update topic
for an incomplete existing owner over a parallel document. Recheck topics that
share lifecycle, contracts, state, data ownership, failure behavior, or
consumers even when their names differ.

Review canonical `document` paths and the complete typed relationship graph.
Reject duplicate paths, unknown targets, isolated nodes, navigation-only
reciprocal edges, vague `related-to`, and predicates unsupported by the
responsibility descriptions. The reviewed graph is authoritative for
production and deterministic assembly.

Preserve every `source_topic_id`; merge by placing several sources in one
topic. A source may appear in several topics only when its described
responsibility genuinely participates in several independently useful
architectural boundaries. Do not copy or invent file paths: the materializer
owns files.

For exhaustive work, return uncovered discovery gaps in `open_leads` and no
`deferred_leads`. For increment work, preserve the supplied deferred leads
exactly and return no open leads.

If the provisional mapping needs no correction, avoid repeating it:

```json
{
  "decision": "accept",
  "review": {
    "existing_coverage_checked": true,
    "cross_batch_duplicates_checked": true,
    "granularity_checked": true,
    "notes": "Concise explanation of coverage and granularity checks."
  }
}
```

If correction is necessary, write `decision: replace`, the complete corrected
mapping under `mapping`, and the same `review` object. Do not emit a patch or
repeat the provisional mapping for `accept`.

Set an attestation only after completing that check. The materializer rejects an unreviewed synthesizer result. Terminate without editing the corpus, Spine, or campaign.
