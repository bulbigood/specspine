# SpecSpine Map topic-reduction contract

Read one synthesis batch and reduce its `source_topics` by semantic
responsibility. Each source contains the scout's title, responsibility, reason,
and discovery-lead context. IDs are references only; never infer architecture
from their spelling.

Merge sources that describe the same durable responsibility or boundary.
Preserve separate responsibilities when they evolve, fail, own state, or serve
consumers independently. Do not classify coverage or supporting evidence, read
the repository, copy file paths, create new discovery leads, or edit any other
artifact.

Write exactly:

```json
{
  "batch_id": "batch-0001",
  "candidates": [
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

Disposition every input `source_id` exactly once. Candidate IDs must be unique
within the batch. Reread the result for directory-shaped boundaries and local
duplicates, then terminate.
