# Documentation-first exhaustive seeding

Use this protocol when exhaustive Map starts with an existing Spine containing
one or more specification nodes besides `README.md`.

## Build the initial frontier

Before inspecting production source:

1. Read `README.md` and every linked or otherwise present Markdown node.
2. Assess the existing graph as architecture memory, not as presumed truth.
3. Identify bounded directions from partial/unmapped coverage, open questions,
   broad owners, weak relationships, missing failure/lifecycle/interface/data/
   operational depth, stale evidence, navigation gaps, or inconsistencies.
4. Make every direction strictly more precise than its source document. Record
   a depth witness with the exact section/ID/relation/question/claim anchor,
   what it establishes, one narrower unknown, evidence that would close it,
   and excluded sibling concerns.
   The branch `question` must exactly equal `depth.unknown`, so dispatch cannot
   widen a valid witness.
   A document title, its whole responsibility, or “map this area more deeply”
   is not a valid direction. Structural repair signals still need a precise
   affected anchor and bounded completion evidence.
5. Group related signals under the smallest existing canonical owner or
   coherent owner set. Do not recreate top-level source domains such as
   “backend”, “frontend”, or “services” unless the Spine itself exposes that
   unresolved boundary.
6. Save the complete document inventory and directions as JSON:

```json
{
  "evidence_inspected": ["README.md", "identity.md", "sessions.md"],
  "directions": [
    {"id": "identity-session-failures",
     "question": "Who owns recovery when expiry races with refresh?",
     "documents": ["identity.md", "sessions.md"],
     "signals": [{"type": "missing_depth",
                  "detail": "Normal expiry is covered; recovery is absent"}],
     "depth": {
       "anchor_document": "sessions.md",
       "anchor": "Lifecycle / active-to-expired transition",
       "known": "Creation and normal expiry ownership are established",
       "unknown": "Who owns recovery when expiry races with refresh?",
       "completion_evidence": "Call paths and recovery state transitions",
       "excludes": ["token issuance", "login", "storage deployment"]}}
  ]
}
```

Allowed signal types are `coverage_gap`, `open_question`, `broad_owner`,
`weak_relationship`, `missing_depth`, `stale_evidence`, `navigation_gap`, and
`semantic_inconsistency`.

If the documents expose no useful direction, use an empty `directions` list
plus `terminal_reason: "no documentation-derived direction: <reason>"`. This
records the negative result without manufacturing a gap; the later source
blind-spot pass still runs.

Initialize and seed the campaign before assigning any producer:

```text
python3 <map-skill-root>/scripts/campaign.py init \
  <campaign> --scope <scope> --root-question <question> \
  --spine-state existing
python3 <map-skill-root>/scripts/campaign.py seed-from-spine \
  <campaign> <spine-root> <documentation-plan.json>
```

`seed-from-spine` records document digests and atomically rejects an incomplete
inventory or malformed depth witness. The root must verify that the unknown is
semantically narrower; the script verifies only shape and provenance. A branch
may replace a document, create a justified child, or report local saturation.

## Use source after seeding

Give each producer its planned owner documents, signals, and question. The
producer reads source only to test that bounded gap, establish observations,
and discover directly exposed child responsibilities.

After these branches drain, use source discovery only for areas without a
credible owner or architecture the documents could not expose. Drain those
blind spots before saturation.

After publications and navigation normalization, read the complete live Spine
again and submit the same plan shape through:

```text
python3 <map-skill-root>/scripts/campaign.py documentation-pass \
  <campaign> <spine-root> <documentation-plan.json>
```

A nonempty direction list creates new queued branches and invalidates prior
terminal evidence. An empty result records final document digests. Any later
publication or frontier change invalidates that pass, so repeat it until the
recorded direction list is empty at the current frontier epoch.

Each pass applies the depth witness to richer live documents. If an answer
exposes a narrower unresolved mechanism, transition, failure, ownership, or
consequence, enqueue a new ID and anchor. This is the recursive deepening
mechanism. Never repeat a prior question or reopen the whole owner.

Do not treat a `Mapped` label, document count, or broad overview as proof of
depth. Conversely, do not split a useful broad owner merely because it covers
several responsibilities; create a child only when the normal decomposition
and quality gates justify one.
