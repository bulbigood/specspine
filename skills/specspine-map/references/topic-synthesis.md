# SpecSpine Map topic-synthesis contract

In one fresh isolated context, read the complete validated planning corpus and
produce the sole semantic producer frontier. The corpus pages are neutral
pagination; ignore page boundaries.

Merge provisional topics that express one durable responsibility even when
their files or names differ. Split topics that combine independently evolving
responsibilities. Remove directory-shaped `models`, `utils`, `services`, file,
framework, and tooling categories unless repository evidence establishes a
project-specific architectural contract. Resolve overlaps by responsibility,
interfaces, lifecycle, data ownership, and consumers. Inspect targeted
repository evidence when candidate descriptions are insufficient.

After forming the semantic candidate set, process every topic one at a time.
Retrieve relevant context from the existing `<spine-root>` using the available
SpecSpine semantic discovery/extraction workflow. Compare responsibility and
boundaries, not names alone. A topic is `covered` only when existing canonical
documents and their semantic claims collectively describe that responsibility
well enough that another producer would create no missing architectural
observation. Record the exact documents and claim IDs supporting that decision.
Otherwise keep the topic in `topics` for a producer. Never treat navigation
text, a filename match, a broad neighboring owner, or an unsupported claim as
coverage.

Repository evidence cannot create normative intent. Topic text states an
observed responsibility and why it is architecturally useful. A file may occur
in multiple final topics when it genuinely participates in multiple
responsibilities. Put a file in `supporting` only when no final topic needs it.
Every production file from the corpus must remain accounted for.

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
  ]
}
```

Final IDs are stable lowercase kebab-case and semantic, never page, shard, or
path identifiers. Each topic contains at most 80 files; split by a real
responsibility boundary when larger. Reread the entire result once to merge
duplicates, detect missing cross-page concepts, remove source-tree mirroring,
verify every candidate received a Spine coverage decision, and verify complete
file disposition. Only `topics` becomes the producer frontier; `covered`
remains auditable evidence. Do not edit the Spine or campaign.
