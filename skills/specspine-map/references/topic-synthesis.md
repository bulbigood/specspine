# SpecSpine Map global topic-synthesis contract
Read every `source_topic` in the global synthesis packet and produce one
semantic mapping. Source titles, responsibilities, reasons, and shared
discovery context through `leads` define the input; IDs are references only.
Never read, copy, or invent file lists. Discovery hierarchy and lead
boundaries are provenance, not architecture.
Use only predicates listed in `allowed_relationship_types` from the synthesis packet unless a genuinely project-specific `x-*` relation is unavoidable. `existing_owners` maps current owner IDs to canonical documents and titles; use it for existing graph targets and uncovered owner updates.
First perform one global semantic pass across all sources. Merge sources that
express one durable responsibility even when parents or names differ. Keep
independently evolving responsibilities separate. Remove directory-shaped,
framework, tooling, `models`, `utils`, and `services` categories unless the
descriptions establish a project-specific architectural contract. Resolve
overlap by responsibility, interfaces, lifecycle, state, data ownership,
failures, and consumers. Then enforce the operation's inclusion and exclusion
rules, classify existing coverage, and construct the complete graph.
Do not create a topic merely for a facet such as failures, configuration,
interfaces, tests, or observability. Keep that facet with its responsible
owner unless the sources establish an independently evolving mechanism with
its own lifecycle, state, interface, and consumers. Before emitting the
mapping, compare every pair of topics and assign each observation to exactly
one canonical responsibility; relationships may reference a neighbor but may
not duplicate its owned behavior.

For exhaustive completion, detect responsibilities or boundaries exposed but
never expanded and place them in `open_leads`; deterministic materialization
retains them as deferred work without another discovery or synthesis pass.
Reproduce corpus `deferred_leads` exactly. For increment completion, return no
open leads and reproduce corpus `deferred_leads` exactly.
For exhaustive completion, audit peer families exposed by evidence in
`peer_family_review`; each must be dispositioned or retained as an open lead.
Allowed statuses are exactly `accounted`, `none-found`, and `not-required`.
Use `none-found` only with a concrete reason; increment may use `not-required`.
Use `accounted` when descriptions expose named peer members: every member must
remain explicit in a final topic responsibility, be separately covered or
supporting, or have an `open_lead`. Merging peers under one shared owner must
not erase their names or distinct observable behavior.

When discovery is closed, classify every canonical topic in sequence. For
each, use SpecSpine semantic extraction to find candidate owners, then compare
responsibility, boundaries, lifecycle, state, interfaces, and exact claims.
Record the result before evaluating the next topic. Mark `covered` only when
exact documents and claims collectively make another producer unnecessary.
Accepted prose and normative claims may cover evidence without an `OBS`;
classify this as `covered-by-intent` without requiring owner evidence paths.
When an owner has a material gap, keep one uncovered update topic for it. An empty Spine
covers nothing; an existing Spine with zero covered topics requires explicit
review rather than silent acceptance.
Map updates an existing owner only in place, preserving its ID, path, kind, accepted claims, and boundary. Never split, merge, move, rename, replace, redistribute, or add child owners to decompose existing documents; only Evolve reorganizes the Spine. Preserve suggested topology changes as evidence or an open question.
Write exactly:

```json
{
  "topics": [
    {
      "id": "session-lifecycle",
      "document": "sessions/session-lifecycle.md",
      "title": "Session lifecycle",
      "responsibility": "Creates, validates, renews, and revokes sessions.",
      "reason": "These sources describe one durable stateful lifecycle.",
      "relationships": [
        {
          "type": "depends-on",
          "target": "audit-retention",
          "reason": "Session transitions emit retained audit events."
        }
      ],
      "source_topic_ids": [
        "session-runtime/session-creation",
        "session-storage/session-revocation"
      ]
    }
  ],
  "covered": [
    {
      "id": "audit-retention",
      "document": "security/audit.md",
      "title": "Audit retention",
      "responsibility": "Retains and expires security audit events.",
      "reason": "This source owns one durable security lifecycle.",
      "relationships": [],
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
  "deferred_leads": [],
  "peer_family_review": {"status": "accounted", "reason": "Every named transport peer remains explicit in a final owner or disposition.", "source_topic_ids": ["transport-runtime/http-and-grpc"], "open_lead_ids": []}
}
```
An open lead contains exactly `id`, `title`, `question`, `reason`, and
`seed_files`. Final IDs are stable semantic lowercase kebab-case. Disposition
every source topic as uncovered, covered, or supporting. Preserve one source
in several final topics only for genuine independently useful responsibilities.
Assign each topic one canonical `document` and define its directed graph using
only `type`, target owner `id`, and concrete `reason`. Audit inputs, outputs,
dependencies, consumers, owned data, and runtime coordination across all topics.
Use predicates operationally: `publishes` makes an event, intent, or result available without implying mutation; `consumes` processes such output;
`reads-from` obtains target-owned data; `writes-to` directly mutates it;
`owns-data` assigns authoritative state ownership; `depends-on` means the source
cannot fulfill its responsibility without the target; `migrates-from` points
from the successor contract or format to its predecessor. Use `related-to` only
when no precise predicate is justified. Every reason names the concrete event,
intent, state, data, or contract and its architectural consequence.
Add each high-confidence useful edge once; omit a doubtful edge or preserve a
question. Reciprocal edges require two distinct directed interactions with
different objects or consequences, never backlinks or navigation. A topic may
remain isolated only after this explicit audit. Targets are planned or existing owners.
Reread for duplicates, missing data/control-flow edges, weak edges, and unsupported coverage. Do not edit inputs; materialization publishes the canonical plan.

State the disposition in existing reason fields: `covered-by-intent`,
`implementation-freedom`, `retain-observation`, `retain-divergence`,
`retain-inference`, `retain-open-question`, or `implementation-detail`.
