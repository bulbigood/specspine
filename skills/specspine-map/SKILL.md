---
name: specspine-map
description: "Map architecture-significant deltas between brownfield repository reality and accepted SpecSpine intent. Use for one focused survey, deepening, refresh, or drift increment; a broad repository survey; or exhaustive comparison of a named architectural scope or whole repository. Discover semantic responsibilities, classify evidence against existing intent, retain only material gaps, divergences, uncertainty, and navigation observations, record bounded inspection coverage, integrate centrally, and verify the selected completion claim. Do not duplicate matching intent, infer intended architecture, audit general integrity, implement code, or claim code/spec conformance."
---

# SpecSpine Map
Turn repository evidence into a verified delta against SpecSpine intent through one
operation:

```text
scope → discovery → synthesis → production → integration → verification
```
Repository evidence establishes `OBS`, not accepted intent. Preserve
uncertainty and code/spec disagreement; never infer decisions, constraints,
requirements, guarantees, or conformance.
Map may add observations to an existing canonical owner, but it must not split,
merge, move, rename, replace, decompose, or redistribute existing Spine
documents. Reorganization of accepted ownership and document topology belongs
exclusively to Evolve.
An `OBS` is an exception layer, not a code mirror. Retain one only for an
architecture-significant intent gap, divergence, unresolved question, or
surprising owner/boundary. Evidence already represented by intent is
`covered-by-intent`: update inspection coverage without an `OBS`. Discard
compatible implementation freedom and source detail.
## Operation

Define two independent axes before discovery:

- `scope.kind: semantic` for a named area or question; `repository` when the
  whole repository is the search boundary.
- `completion.kind: increment` for one coherent change; `exhaustive` for a
  completeness request.

Increment intents are `survey`, `deepen`, `refresh`, and `drift`. Repository
increment supports only `survey`.

Both completion policies use the same artifacts and state machine:

- increment settles one initial discovery layer, preserves adjacent work in
  `deferred_leads`, forbids derived ToDo, and ends at `increment_verified`;
- exhaustive scouts close their assigned semantic boundaries internally,
  dispatch only justified unresolved fallback, forbid deferral, and end at
  `scope_verified`.

Neither terminal claims that no conceivable architectural concept exists.
`increment_verified` never claims scope completeness.
For exhaustive completion, every peer family exposed by inspected evidence
must be dispositioned or retained as an `open_lead`; otherwise Map cannot reach
`scope_verified`.
## Required references

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims or disagreement.
- Read [references/spec-format.md](references/spec-format.md) before changing
  specifications.
- Use [references/spec-glossary.md](references/spec-glossary.md) as the index
  of reserved identifiers, tokens, kinds, relations, and manifest values.
- Read `specspine.json.presentation` before producing Markdown; render its
  configured headings and order while preserving canonical v3 meaning.
- Read [references/mapping-method.md](references/mapping-method.md) before
  discovery.
- Read [references/orchestration.md](references/orchestration.md) completely;
  it defines the durable CLI lifecycle.
- Give isolated workers only their phase contract:
  [discovery-planner.md](references/discovery-planner.md),
  [discovery-task.md](references/discovery-task.md),
  [frontier-curation.md](references/frontier-curation.md),
  [topic-synthesis.md](references/topic-synthesis.md),
  [producer-task.md](references/producer-task.md), or
  [repository-coverage.md](references/repository-coverage.md).
- Read [integration-pass.md](references/integration-pass.md) only when
  deterministic assembly reports `needs_semantic_review`.
- Start new files from `assets/templates/`; omit empty sections.
## Authorities

Discovery finds evidence; synthesis defines topics, canonical documents, the
typed graph, and existing coverage; producers verify one topic and stage its
assigned document; deterministic assembly publishes clean results. Root handles
only receipts, state transitions, and explicit semantic exceptions. An isolated
planner chooses the initial semantic search boundaries for every scope. Root
does not inspect production code or ingest discovery content. Discovery
hierarchy, paths, and filenames never define architecture.
Scouts write semantic drafts; `discovery_finalize.py` alone derives and
atomically publishes canonical discovery results.

`orchestration.md` owns worker tiers, wave sizing, runtime placement, recovery,
terminal gates, and publication. Follow it without restating those rules here.
Producer acceptance never edits the live Spine; deterministic integration
checks and publishes one private workspace atomically. Do not invoke Doctor
inside Map.

The synthesizer operates on every scout description and provenance ID in one
global packet, never on bulk file lists. It performs global deduplication,
coverage classification, granularity, and graph construction in one task.
`synthesis.py` alone prepares that compact packet, resolves IDs back to corpus
evidence, reports suspicious coverage or granularity, and atomically writes
the sole canonical topic plan. Semantic diagnostics are advisory: Map favors
prompt coverage and leaves later graph refinement to Doctor or Evolve.
Only whole-repository exhaustive mapping adds an isolated topology coverage
audit after synthesis. It looks for missing architectural roots, not file
coverage, and reopens only concrete gaps.
