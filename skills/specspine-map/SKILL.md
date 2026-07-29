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
## Required references

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims or disagreement.
- Read [references/spec-format.md](references/spec-format.md) before changing
  specifications.
- Read `specspine.json.presentation` before producing Markdown; render its
  configured headings and order while preserving canonical v3 meaning.
- Read [references/mapping-method.md](references/mapping-method.md) before
  discovery.
- Read [references/orchestration.md](references/orchestration.md) completely;
  it defines the durable CLI lifecycle.
- Give isolated workers only their phase contract:
  [discovery-task.md](references/discovery-task.md),
  [frontier-curation.md](references/frontier-curation.md),
  [topic-synthesis.md](references/topic-synthesis.md),
  [producer-task.md](references/producer-task.md).
- Read [integration-pass.md](references/integration-pass.md) before publishing.
- Start new files from `assets/templates/`; omit empty sections.
## Authorities

Discovery finds evidence; synthesis defines topics, canonical documents, the
typed graph, and existing coverage; producers verify one topic and stage its
assigned document; deterministic assembly publishes clean results. Root handles
only explicit semantic exceptions. Discovery
hierarchy, inventory pages, paths, and filenames never define architecture.
Scouts write semantic drafts; `discovery_finalize.py` alone derives and
atomically publishes canonical discovery results.

Use a flat production-file inventory only as a neutral accelerator for
repository scope. It grants no grouping, ownership, coverage, or completion.
It is exhaustive by default; an explicit test-only limit creates a truncated
vertical slice that cannot support a repository completeness claim.

For exhaustive work, use fresh isolated weak-tier scouts; medium-tier
curators; strong-tier one-shot producers; and one strong-tier global
synthesizer. Scout subwaves contain at most
ten and must also fit the runtime's available subagent slots; reserve the root
slot when capacity includes it. Producer waves contain at most ten and must
also fit available slots while reserving root. Never
refill a settled strict wave. An increment may execute the same contracts
serially in root. If the required execution tier is unavailable, preserve the
campaign and report it blocked.

Before semantic discovery, derive one to ten independent search boundaries
from operation breadth without reading production code. Runtime capacity
controls how many run per strict subwave, never how many planned boundaries
must be completed. Repository discovery derives initial packets from the
neutral inventory accelerator without a duplicate whole-repository scout.
Complete and validate every initial packet
before frontier curation.

Keep every Map campaign and temporary artifact under
`<workspace>/.specspine/map`; never use agent-global or OS temporary storage.
The runtime directory is excluded from discovery and may contain multiple
named campaign directories. Run `campaign.py next-action`
before final answers; `may_finish: false` forbids finishing unless `may_pause:
true`. On resume, harvest
retained assigned tasks before releasing only those without a valid
atomic handoff; never restart accepted or harvestable work. Before repeating
discovery or synthesis, run `campaign.py recover`: trust phase manifests and
input digests, discard unfinished AI drafts, and repeat only missing results.
Never initialize the same incomplete operation again. Reopen a confirmed
mechanical false blocker with `campaign.py retry-blocked`; preserve every other
accepted task and artifact.
Producer acceptance never edits the live Spine. Integrate accepted handoffs in
one private workspace, run the v3 checker, then publish the workspace and
ledger transition atomically. Do not invoke Doctor inside Map.

The synthesizer operates on every scout description and provenance ID in one
global packet, never on bulk file lists. It performs global deduplication,
coverage classification, granularity, and graph construction in one task.
`synthesis.py` alone prepares that compact packet, resolves IDs back to corpus
evidence, reports suspicious coverage or granularity, and atomically writes
the sole canonical topic plan. Semantic diagnostics are advisory: Map favors
prompt coverage and leaves later graph refinement to Doctor or Evolve.
