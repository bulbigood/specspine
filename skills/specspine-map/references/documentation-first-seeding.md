# Documentation-first exhaustive seeding

Use this protocol when exhaustive Map starts with an existing Spine containing
one or more specification nodes besides `README.md`.

## Build the initial frontier

Before inspecting production source:

1. Read `README.md` and every linked or otherwise present Markdown node.
2. Assess the existing graph as architecture memory, not as presumed truth.
3. Identify bounded directions from documentation signals:
   - `Partially mapped` and `Unmapped` coverage;
   - concrete `Open questions`;
   - broad overview owners whose children or depth remain uncertain;
   - weak or generic relationships that obscure ownership or impact;
   - missing failure, lifecycle, interface, data-ownership, or operational
     depth where the concept requires it;
   - stale evidence baselines, navigation gaps, and semantic inconsistencies.
4. Group related signals under the smallest existing canonical owner or
   coherent owner set. Do not recreate top-level source domains such as
   “backend”, “frontend”, or “services” unless the Spine itself exposes that
   unresolved boundary.
5. Save the complete document inventory and directions as JSON:

```json
{
  "evidence_inspected": ["README.md", "identity.md", "sessions.md"],
  "directions": [
    {
      "id": "identity-session-failures",
      "question": "Are session failure and recovery boundaries sufficient?",
      "documents": ["identity.md", "sessions.md"],
      "signals": [
        {
          "type": "missing_depth",
          "detail": "The owner describes normal behavior but not expiry or recovery"
        }
      ]
    }
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

`seed-from-spine` rejects an incomplete Markdown inventory, records document
digests, and creates queued branches atomically. Every planned branch remains
an investigation: the producer may replace a document, create a justified
child, or report evidence-based local saturation.

## Use source after seeding

Give each producer its planned owner documents, signals, and question. The
producer reads source only to test that bounded gap, establish observations,
and discover directly exposed child responsibilities.

After all documentation-derived branches drain, perform the normal source-level
repeat discovery pass. Its purpose is now limited to finding production areas
with no credible documented owner and detecting architecture that existing
documents could not expose. Add such blind spots as new branches and drain
them before saturation.

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

Do not treat a `Mapped` label, document count, or broad overview as proof of
depth. Conversely, do not split a useful broad owner merely because it covers
several responsibilities; create a child only when the normal decomposition
and quality gates justify one.
