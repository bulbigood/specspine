# SpecSpine Map topic-reduction contract

Read one synthesis batch and reduce its `source_topics` by semantic
responsibility. Each source contains the scout's title, responsibility, reason,
and a `lead_id`; resolve shared discovery context through the packet's `leads`
table. IDs are references only; never infer architecture from their spelling.

Merge sources that describe the same durable responsibility or boundary.
Preserve separate responsibilities when they evolve, fail, own state, or serve
consumers independently. Do not classify coverage or supporting evidence, read
the repository, copy file paths, create new discovery leads, or edit any other
artifact.

Return unchanged singleton sources by ID only. The script copies their
semantic fields without model rewriting. Write merged descriptions only when
two or more sources describe one owner:

```json
{
  "batch_id": "batch-0001",
  "passthrough": ["session-runtime/session-formatting"],
  "merged": [
    {
      "id": "session-lifecycle",
      "title": "Session lifecycle",
      "responsibility": "Creates, validates, renews, and revokes sessions.",
      "reason": "These sources describe one stateful lifecycle owner.",
      "source_topic_ids": [
        "session-runtime/session-creation",
        "session-storage/session-revocation"
      ]
    }
  ]
}
```

Disposition every input `source_id` exactly once across `passthrough` and
`merged`. Every merged candidate needs at least two sources; its ID must be
unique within the batch. Reread the result for directory-shaped boundaries
and local duplicates, then terminate.
