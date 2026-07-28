# SpecSpine Map topic-synthesis contract

In one fresh isolated context, read the complete validated discovery corpus and
produce the sole semantic producer frontier. The discovery hierarchy, inventory
pages, and lead boundaries are provenance, not architecture.

First enforce the declared inclusion and exclusion rules. Merge provisional
topics that express one durable responsibility even when files, parents, or
names differ. Split topics that combine independently evolving
responsibilities. Remove directory-shaped `models`, `utils`, `services`, file,
framework, and tooling categories unless repository evidence establishes a
project-specific architectural contract. Resolve overlaps by responsibility,
interfaces, lifecycle, state, data ownership, failures, and consumers. Inspect
targeted repository evidence when candidate descriptions are insufficient.

Before coverage classification, apply the completion policy. For exhaustive
completion, check the whole corpus for a responsibility,
cross-topic reference, or boundary that discovery exposed but never expanded.
Put each such gap in `open_leads`; do not compensate by creating a vague topic.
When `open_leads` is nonempty, the orchestrator must return them to discovery
and rerun synthesis after the frontier closes.

For increment completion, do not reopen discovery. Reproduce the corpus
`deferred_leads` exactly and keep any additional adjacent direction inside that
set only when it was dispositioned by frontier curation. `open_leads` must be
empty. Do not turn a deferred lead into a producer topic.

When discovery is closed, process every semantic topic one at a time. Retrieve
relevant context from the existing `<spine-root>` using the available
SpecSpine semantic discovery/extraction workflow. Compare responsibility and
boundaries, not names alone. A topic is `covered` only when existing canonical
documents and their semantic claims collectively describe that responsibility
well enough that another producer would create no missing architectural
observation. Record exact documents and claim IDs. Otherwise keep it in
`topics`. Never treat navigation text, a filename match, a broad neighboring
owner, or an unsupported claim as coverage.

Repository evidence cannot create normative intent. A file may occur in
multiple final topics when it genuinely participates in multiple
responsibilities. Put a file in `supporting` only when no final topic needs it.
Every evidence file from the corpus must remain accounted for.

Write `topic-plan.json` with exactly:

```json
{
  "topics": [
    {
      "id": "session-lifecycle",
      "title": "Session lifecycle",
      "responsibility": "Creates, validates, renews, and revokes application sessions.",
      "reason": "This boundary owns externally significant state transitions and persistence.",
      "files": ["src/session/service.go", "src/session/store.go"]
    }
  ],
  "covered": [
    {
      "id": "audit-retention",
      "title": "Audit retention",
      "responsibility": "Retains and expires security audit events.",
      "reason": "This boundary owns a durable security lifecycle.",
      "files": ["src/audit/store.go"],
      "coverage_reason": "The canonical audit owner already specifies retention and expiry.",
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
      "files": ["src/session/format.go"]
    }
  ],
  "open_leads": [],
  "deferred_leads": []
}
```

An open lead uses exactly `id`, `title`, `question`, `reason`, and
`seed_files`. Final IDs are stable lowercase kebab-case and semantic, never
page, shard, hierarchy, or path identifiers. Each topic contains at most 80
files; split only at a real responsibility boundary. Reread the entire result
once to merge duplicates, detect missing cross-lead concepts, remove source-tree
mirroring, verify every candidate received a Spine coverage decision, and
verify complete evidence disposition. Only `topics` becomes the producer
frontier; `covered` remains auditable evidence. Do not edit the Spine or
campaign.
