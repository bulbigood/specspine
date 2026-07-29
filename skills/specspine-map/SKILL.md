---
name: specspine-map
description: "Map observed brownfield architecture into a linked Markdown SpecSpine v3. Use for one focused survey, deepening, refresh, or drift increment; a broad repository survey; or exhaustive documentation of a named architectural scope or whole repository. Discover semantic responsibilities, filter existing SpecSpine coverage, produce missing observations, integrate centrally, and verify the selected completion claim. Do not infer intended architecture, audit general integrity, implement code, or claim code/spec conformance."
---

# SpecSpine Map

Turn repository evidence into verified SpecSpine observations through one
operation:

```text
scope → discovery → synthesis → production → integration → verification
```

Repository evidence establishes `OBS`, not accepted intent. Preserve
uncertainty and code/spec disagreement; never infer decisions, constraints,
requirements, guarantees, or conformance.

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
- Read [references/mapping-method.md](references/mapping-method.md) before
  discovery.
- Read [references/orchestration.md](references/orchestration.md) completely;
  it defines the durable CLI lifecycle.
- Give isolated workers only their phase contract:
  [discovery-task.md](references/discovery-task.md),
  [frontier-curation.md](references/frontier-curation.md),
  [topic-reduction.md](references/topic-reduction.md),
  [topic-synthesis.md](references/topic-synthesis.md),
  [topic-review.md](references/topic-review.md), or
  [producer-task.md](references/producer-task.md).
- Read [integration-pass.md](references/integration-pass.md) before publishing.
- Start new files from `assets/templates/`; omit empty sections.
## Authorities

Discovery finds evidence; synthesis alone defines semantic topics and checks
existing coverage; producers verify one topic and stage private output; root
alone chooses canonical ownership and publishes a checked workspace. Discovery
hierarchy, inventory pages, paths, and filenames never define architecture.
Scouts write semantic drafts; `discovery_finalize.py` alone derives and
atomically publishes canonical discovery results.

Use a flat production-file inventory only as a neutral accelerator for
repository scope. It grants no grouping, ownership, coverage, or completion.
It is exhaustive by default; an explicit test-only limit creates a truncated
vertical slice that cannot support a repository completeness claim.

For exhaustive work, use fresh isolated weak-tier scouts, medium-tier
curators, topic reducers, reviewers, and one-shot producers, and one fresh
strong-tier global synthesizer. Scout subwaves contain at most
ten and must also fit the runtime's available subagent slots; reserve the root
slot when capacity includes it. Producer waves contain at most five. Never
refill a settled strict wave. An increment may execute the same contracts
serially in root. If the required execution tier is unavailable, preserve the
campaign and report it blocked.

Keep campaign state in the platform's persistent private runtime-data root,
never the project or OS temporary storage. Run `campaign.py next-action`
before final answers; `may_finish: false` forbids finishing unless `may_pause:
true`. On resume, harvest
retained assigned tasks before releasing only those without a valid
atomic handoff; never restart accepted or harvestable work. Before repeating
discovery or synthesis, run `campaign.py recover`: trust phase manifests and
input digests, discard unfinished AI drafts, and repeat only missing results.
Producer acceptance never edits the live Spine. Integrate accepted handoffs in
one private workspace, run the v3 checker, then publish the workspace and
ledger transition atomically. Do not invoke Doctor inside Map.

Synthesis agents operate on scout descriptions and provenance IDs, never on
bulk file lists. `synthesis.py` alone copies singleton semantics, validates
reducer coverage, exposes original descriptions only for reducer merges,
resolves IDs back to corpus evidence, requires independent review attestation,
reports suspicious coverage or granularity, and atomically writes the sole
canonical topic plan.
