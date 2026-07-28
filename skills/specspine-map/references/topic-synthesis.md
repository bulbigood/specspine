# SpecSpine Map global topic-synthesis contract

Read the compact candidates emitted by all topic reducers and produce one
semantic mapping. Candidate titles, responsibilities, reasons, and scout
provenance define the input; IDs are references only. Never read, copy, or
invent file lists. Discovery hierarchy and lead boundaries are provenance, not
architecture.

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

When discovery is closed, classify every canonical topic against the existing
Spine one at a time using SpecSpine semantic extraction. Compare responsibility
and boundaries, not names. Mark `covered` only when exact documents and claims
collectively make another producer unnecessary. An empty Spine covers nothing.

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
campaign, or repository.
