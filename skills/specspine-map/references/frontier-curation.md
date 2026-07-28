# SpecSpine Map frontier-curation contract

In one fresh isolated context, compare every child-lead proposal from the
settled discovery level with the compact registry of already queued and
completed leads. Apply the operator scope's inclusion and exclusion rules.
Do not inspect source deeply, classify coverage, create producer topics, or edit
the repository, Spine, campaign, results, or prior packets.

Merge proposals that ask the same responsibility or boundary question even
when names, parents, or seed files differ. Preserve all proposal references and
parent IDs in the one canonical queued lead. Mark a proposal `duplicate` only
when an existing or newly queued lead will perform the same investigation.
Mark it `out_of_scope` only with a concrete scope-rule reason. Do not use page,
directory, framework-layer, or hierarchy names as semantic identity.

Apply the packet completion policy:

- exhaustive: queue every remaining unique in-scope proposal; never defer;
- increment: queue none; merge remaining in-scope proposals into canonical
  `defer` decisions with their lead content and a concrete deferral reason.

Write exactly:

```json
{
  "decisions": [
    {
      "disposition": "defer",
      "sources": ["kafka-runtime/schema-registry"],
      "lead": {
        "id": "kafka-schema-ownership",
        "title": "Kafka schema ownership",
        "question": "Who evolves Kafka event schemas?",
        "reason": "The mapped runtime exposes an adjacent contract boundary.",
        "parent_ids": ["kafka-runtime"],
        "seed_files": ["pkg/kafka/schema.go"]
      },
      "reason": "Increment completion records adjacent work without expanding it."
    },
    {
      "disposition": "queue",
      "sources": [
        "kafka-consumer-lifecycle/offset-recovery",
        "alert-consumer/replay-offsets"
      ],
      "lead": {
        "id": "kafka-offset-recovery",
        "title": "Kafka offset recovery",
        "question": "Which component owns offset recovery after handler failure?",
        "reason": "Two consumers delegate one observable recovery boundary.",
        "parent_ids": ["alert-consumer", "kafka-consumer-lifecycle"],
        "seed_files": ["pkg/kafka/consumer.go"]
      }
    },
    {
      "disposition": "duplicate",
      "sources": ["notification-runtime/kafka-consumer"],
      "target": "kafka-consumer-lifecycle",
      "reason": "The existing lead investigates the same consumer lifecycle."
    },
    {
      "disposition": "out_of_scope",
      "sources": ["kafka-runtime/unrelated-database"],
      "reason": "The database shares deployment infrastructure but has no Kafka responsibility."
    }
  ]
}
```

Disposition every proposal exactly once. Queue no lead already present in the
registry. A safety depth, agent, time, or topic budget never grants closure:
if it prevents a required lead, report the campaign blocked instead of marking
the proposal duplicate or out of scope. Reread the whole decision list for
semantic duplicates and scope leakage, then terminate without messaging other
agents.
