# SpecSpine Map discovery-scout contract

Handle exactly one discovery lead. Read the packet operation and scope before
searching. Read `<spine-root>/README.md` for system vocabulary and
orientation, then inspect the lead's seed files and search the repository for
directly related responsibilities, registrations, callers, dependencies,
interfaces, state, failures, deployment, operations, schemas, and tests.

The lead is one semantic expansion step, not a future specification or a path
group. Follow evidence outside its seed files when it remains inside the
inclusion rule. Do not cross the exclusion rule merely because two components
share infrastructure. Do not edit the repository, Spine, campaign, packet, or
another result.

Classify inspected files into provisional architectural topics or `supporting`.
Propose a child lead only for an in-scope responsibility or boundary that needs
another focused expansion. A child is discovery work, not a producer task.
Never suppress a child merely because a broad existing Spine document mentions
its parent; coverage is decided only after the complete corpus is synthesized.

Use durable responsibilities, capabilities, runtimes, integrations, data
ownership, or project-specific cross-cutting contracts. Do not mirror
directories, generic `models`/`utils`/`services` layers, individual classes,
static assets, or local implementation details. Repository evidence establishes
observations only.

Write the result matching the packet path under `<discovery-results>`:

```json
{
  "lead_id": "kafka-consumer-lifecycle",
  "status": "expanded",
  "reason": "Consumer registration exposes recovery and offset ownership.",
  "inspected": {
    "files": ["pkg/kafka/consumer.go", "services/alerts/events.go"],
    "queries": ["consumer group", "CommitMessages", "retry"]
  },
  "topics": [
    {
      "id": "provisional-consumer-lifecycle",
      "title": "Kafka consumer lifecycle",
      "responsibility": "Starts, stops, and recovers grouped event consumers.",
      "reason": "Registration and shutdown paths establish one runtime boundary.",
      "files": ["pkg/kafka/consumer.go"]
    }
  ],
  "supporting": [
    {
      "reason": "Local event conversion without an independent contract.",
      "files": ["services/alerts/events.go"]
    }
  ],
  "child_leads": [
    {
      "id": "offset-recovery",
      "title": "Offset recovery",
      "question": "Which component owns offset recovery after handler failure?",
      "reason": "The consumer delegates failure recovery outside inspected code.",
      "seed_files": ["pkg/kafka/consumer.go"]
    }
  ]
}
```

Use `expanded` when new leads were exposed and `leaf` when additional reading
would only reproduce local implementation. `duplicate` and `out_of_scope` are
terminal refusals and must contain no topics, supporting files, or child leads.
Every seed file must occur in a topic or supporting entry. Every classified
file must occur in `inspected.files`. Reread the result for unsupported intent,
missing seed files, source-shaped topics, and unjustified scope expansion, then
terminate without messaging other agents.
