# SpecSpine Map global topic-synthesis contract

Read the canonical candidates emitted by all topic reducers and produce one
semantic mapping. Passthrough candidates retain scout semantics mechanically.
For reducer merges, `merged_source_topics` preserves the original descriptions
and resolves shared discovery context through `leads`. Candidate titles,
responsibilities, reasons, and this conditional provenance define the input;
IDs are references only. Never read, copy, or invent file lists. Discovery
hierarchy and lead boundaries are provenance, not architecture.

Enforce the operation's inclusion and exclusion rules. Merge candidates that
express one durable responsibility even when parents or names differ. Keep
independently evolving responsibilities separate. Remove directory-shaped,
framework, tooling, `models`, `utils`, and `services` categories unless the
descriptions establish a project-specific architectural contract. Resolve
overlap by responsibility, interfaces, lifecycle, state, data ownership,
failures, and consumers.

For exhaustive completion, detect responsibilities or boundaries exposed but
never expanded and place them in `open_leads`. Return no `deferred_leads`. For
increment completion, return no open leads and reproduce the corpus
`deferred_leads` exactly.

When discovery is closed, classify every canonical topic in sequence. For
each, use SpecSpine semantic extraction to find candidate owners, then compare
responsibility, boundaries, lifecycle, state, interfaces, and exact claims.
Record the result before evaluating the next topic. Mark `covered` only when
exact documents and claims collectively make another producer unnecessary.
When an owner exists but lacks the observations, keep one uncovered update
topic for that owner instead of inventing a parallel owner. An empty Spine
covers nothing; an existing Spine with zero covered topics requires explicit
review rather than silent acceptance.

Write exactly:

```json
{
  "topics": [
    {
      "id": "session-lifecycle",
      "title": "Session lifecycle",
      "responsibility": "Creates, validates, renews, and revokes sessions.",
      "reason": "These sources describe one durable stateful lifecycle.",
      "source_topic_ids": [
        "session-runtime/session-creation",
        "session-storage/session-revocation"
      ]
    }
  ],
  "covered": [
    {
      "id": "audit-retention",
      "title": "Audit retention",
      "responsibility": "Retains and expires security audit events.",
      "reason": "This source owns one durable security lifecycle.",
      "source_topic_ids": ["audit-storage/audit-retention"],
      "coverage_reason": "The canonical audit owner specifies this lifecycle.",
      "coverage": [
        {
          "document": "security/audit.md",
          "claims": ["OBS-audit-retention", "CON-audit-expiry"]
        }
      ]
    }
  ],
  "supporting": [
    {
      "reason": "Local adapters without an independent durable contract.",
      "source_topic_ids": ["session-runtime/session-formatting"]
    }
  ],
  "open_leads": [],
  "deferred_leads": []
}
```

An open lead contains exactly `id`, `title`, `question`, `reason`, and
`seed_files`. Final IDs are stable semantic lowercase kebab-case. Disposition
every source topic as uncovered, covered, or supporting. Preserve one source
in several final topics only for genuine independently useful responsibilities.
Reread the complete result for cross-batch duplicates, missing boundaries,
source-tree mirroring, and unsupported coverage. Do not edit the Spine, corpus,
campaign, or repository. This is a provisional mapping: do not add `review`;
only the independent reviewer may attest it.
