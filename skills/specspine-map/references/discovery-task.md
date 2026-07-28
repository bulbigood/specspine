# SpecSpine Map discovery-scout contract

Handle exactly one discovery lead. Read the packet operation and scope before
searching. Read `<spine-root>/README.md` for system vocabulary and
orientation, then inspect the lead's seed files and search the repository for
directly related responsibilities, registrations, callers, dependencies,
interfaces, state, failures, deployment, operations, schemas, and tests.

The lead is a semantic search boundary, not a future specification or path
group. Follow evidence outside its seed files when it remains inside the
inclusion rule. Do not cross the exclusion rule merely because two components
share infrastructure. Do not edit the repository, Spine, campaign, packet, or
another result.

Classify inspected files into provisional architectural topics or `supporting`.

For exhaustive completion, maintain a private queue of every directly exposed
in-scope responsibility, owner, interface, state, lifecycle, failure,
deployment, and operational question. Search and classify each item before
finishing. Add newly exposed questions to the same queue and continue until it
is empty. Return all durable fine-grained topics found across this local
closure, not only the first expansion level.

Use `unresolved_leads` only as fallback when a remaining question needs an
independent large investigation, cannot fit safely in the current context, or
crosses into a separately owned semantic boundary. Name the exact unresolved
facet and explain why the current scout could not close it. Never return a
question merely to avoid another local search, repeat a provisional topic, or
represent ordinary navigation.

For increment completion, inspect only the packet's initial semantic layer and
place every directly exposed continuation in `unresolved_leads`; the curator
will defer it. An unresolved lead is discovery work, not a producer task.
Never suppress one merely because a broad existing Spine document mentions its
parent; coverage is decided after synthesis.

Use durable responsibilities, capabilities, runtimes, integrations, data
ownership, or project-specific cross-cutting contracts. Do not mirror
directories, generic `models`/`utils`/`services` layers, individual classes,
static assets, or local implementation details. Repository evidence establishes
observations only.

Write only the supplied private draft. `mapped` means the lead produced a
classification; use `duplicate` or `out_of_scope` only as a terminal semantic
refusal. Do not write `lead_id`, `status`, or `inspected`; the finalizer derives
them.

```json
{
  "disposition": "mapped",
  "reason": "Consumer registration exposes recovery and offset ownership.",
  "queries": ["consumer group", "CommitMessages", "retry"],
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
  "unresolved_leads": [
    {
      "id": "offset-recovery",
      "title": "Offset recovery",
      "question": "Which component owns offset recovery after handler failure?",
      "reason": "The consumer delegates failure recovery outside inspected code.",
      "fallback_kind": "separate_owner",
      "seed_files": ["pkg/kafka/consumer.go"]
    }
  ]
}
```

Every packet seed file must occur in a topic or supporting entry.
`duplicate` and `out_of_scope` require empty topics, supporting, and unresolved
leads. Before returning exhaustive fallback, search its obvious symbols,
callers, registrations, and owner once more. Reread the draft for unsupported
intent, missing seed files, source-shaped topics, and unjustified scope
expansion.

`fallback_kind` is `independent_investigation`, `context_limit`, or
`separate_owner` for exhaustive work, and `increment_continuation` for an
increment.

Run:

```text
python3 <discovery-finalize-script> <packet> <draft> <exact-result>
```

The script canonicalizes paths and publishes the exact result atomically.
If it rejects a semantic omission, correct only the private draft and retry.
Never write or edit the result directly; terminate after `status: ready`
without messaging other agents.
