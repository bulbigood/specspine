---
name: specspine-map
description: Grow repository-observed SpecSpine documentation from brownfield code. Use for an initial survey, “map deepen” or decomposition request, focused refinement, refresh, or drift inspection. A deepen operation discovers and publishes the complete immediate child layer of every selected frontier owner, while preserving deeper work for later calls. Retain only boundary-significant repository evidence and OBS-backed observed edges; never turn code into accepted architecture, implementation documentation, or conformance claims.
---

# SpecSpine Map

Grow the repository-observed owner graph through one coherent operation:

```text
scope → select frontier → inspect one layer → synthesize siblings
      → fill layer → publish atomically → verify
```

Repository evidence establishes `OBS`, `INF`, decomposition status, mapping
frontier, and observed edges. It never establishes accepted intent, canonical
`Relationships`, completeness, or conformance.
An `OBS` is an exception layer, not a code mirror.

## Required resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims.
- Read [references/spec-format.md](references/spec-format.md) before changing
  specifications or the manifest.
- Read [references/owner-operations.md](references/owner-operations.md) before
  selecting an action or changing graph shape.
- Read [references/mapping-method.md](references/mapping-method.md) before
  repository inspection.
- Use [references/spec-glossary.md](references/spec-glossary.md) for reserved
  vocabulary.
- Read `specspine.json.presentation` before writing Markdown.
- Start new owners from `assets/templates/specification.md`.
- Use only bundled `bootstrap_spine.py`, `rebuild_indexes.py`, and
  `check_spine.py` for deterministic writes and validation.

## Authority

Map may:

- add, update, or remove repository-backed `OBS` and `INF`;
- retain an evidence-backed `OQ` or confirmed divergence;
- update inspection and decomposition status;
- persist candidate immediate children under `mapping.frontier`;
- create all observation-only owners in one complete immediate layer;
- publish OBS-backed non-normative `mapping.observed_edges`.

Map must not:

- change accepted prose, normative claims, completeness, or canonical
  `Relationships`;
- split, merge, move, rename, or redistribute accepted owners;
- document private implementation;
- publish a partial sibling layer;
- recursively decompose newly created owners in the same invocation;
- claim code/spec conformance or scope completeness.

For refinement, preserve title, ID, kind, summary, accepted prose,
relationships, and completeness. Never publish repository-derived canonical
`Relationships`.

Evolve owns accepted topology and may later promote observed decomposition or
interaction into canonical relationships.
Map authorizes `refine`, single-owner `expand`, and creation of the complete
child set in `decompose-layer`; it does not authorize any other structural
primitive.

## Mapping model

`mapping.frontier` stores proposed immediate child owners:

```json
{
  "id": "tooltip-interaction",
  "from_owner": "graph-interactions",
  "title": "Tooltip interaction",
  "question": "Which tooltip inputs, outputs, state, and lifecycle cross its boundary?",
  "reason": "Tooltip behavior has consumers and lifecycle distinct from keyboard navigation.",
  "seed_paths": ["src/graph/Tooltip.tsx"]
}
```

`from_owner` is the parent whose responsibility the candidate decomposes.
Dependencies and consumers do not enter frontier merely because they are
adjacent. Candidate IDs remain non-normative until mapped.

`mapping.observed_edges` is the machine-traversable repository graph of
observed owner interactions. Each edge references one canonical `OBS` owned by
one endpoint. It is not an accepted `Relationship`; Evolve may later promote
an observed edge after explicit acceptance.

Every touched manifest area records:

```json
{
  "decomposition": {
    "status": "frontier",
    "reason": "Repository evidence exposes independently useful immediate child boundaries."
  }
}
```

Statuses are `frontier`, `expanded`, and `terminal` as defined by
`owner-operations.md`. Absence means not yet reviewed.

## Workflow

### 1. Scope and action

Resolve `<spine-root>` from the format; otherwise use `specspine`.

Classify inspection as `survey`, `deepen`, `refresh`, or `drift`. Choose:

- `refine` for an explicitly named owner facet, question, refresh, or drift;
- `decompose-layer` for “deepen”, “continue mapping”, “decompose”, “cover the
  next level”, or equivalent wording.

If the Spine is absent, bootstrap its v4 envelope. For an initial survey,
create the smallest useful scope owner, inspect its immediate child layer, and
publish that layer in the same operation. Do not pre-create deeper descendants.

### 2. Select frontier parents

Find canonical owners responsible for the requested scope. For
`decompose-layer`, select all applicable owners whose decomposition is
`frontier` or unreviewed. Do not select:

- an `expanded` overview whose immediate layer is already present;
- a `terminal` owner unless refresh evidence invalidates its reason;
- owners outside the requested scope.

When persisted frontier entries exist for a selected parent, they seed the
immediate child set but do not prove it complete or correct.

### 3. Discover exactly one layer

Inspect enough representative code, interfaces, consumers, state, controls,
lifecycle, failures, tests, and composition roots to find every immediate
independently useful child of each selected parent.

Stop at the child boundary. Do not inspect grandchildren except enough to
decide whether the child is `frontier` or `terminal`.

Classify facts as `covered-by-intent`, `implementation-freedom`,
`retain-observation`, `retain-divergence`, `retain-inference`,
`retain-open-question`, `implementation-detail`, or `frontier-candidate`.
Apply the replacement test.

### 4. Synthesize the sibling set

Perform one global pass across all candidate children before writing:

- keep peers separate when their contracts or reasons to change differ;
- do not group peers because they share a registry, builder, host, framework,
  renderer, package, or helper;
- do not split one responsibility into configuration, failure, interface,
  test, or private-stage owners;
- reuse existing owners;
- distinguish decomposition children from dependencies and consumers;
- require the siblings collectively to account for the parent's delegated
  responsibility.

If the immediate set cannot be resolved confidently, do not publish a partial
layer. Preserve uncertainty and return `blocked`.

### 5. Stage and fill

Draft the complete graph in disposable staging when useful. Create every
missing immediate child and fill it with boundary-significant observations.
For each child:

- describe `Responsibility` as an observed candidate boundary;
- keep code-derived meaning in `Observed` or `Inferred`;
- omit normative sections and canonical `Relationships`;
- register every completeness facet as `missing`;
- add OBS-backed observed edges to its parent and applicable mapped neighbors;
- record accurate inspection coverage;
- mark it `frontier` or `terminal` with a reason.

Consume the selected parents' original frontier entries, add only
grandchild candidates exposed while filling children, and mark parents
`expanded`. A terminal parent produces no children.

Publish all filled siblings and manifest changes as one coherent batch. Never
leave empty canonical drafts.

### 6. Verify

Rebuild indexes after owner creation. Review the complete diff and confirm:

- every selected parent is expanded or terminal;
- the complete immediate sibling set was published;
- no grandchild was created;
- siblings pass the global granularity review;
- accepted meaning and completeness were preserved;
- every observed edge references an existing endpoint-owned `OBS`;
- frontier entries belong only to next-layer parents;
- evidence and inspection coverage are accurate;
- no wording implies acceptance, conformance, or total repository coverage.

Run the mandatory whole-Spine gate:

```text
python3 <skill>/scripts/check_spine.py <spine-root> \
  --repository-root <repository-root>
```

Correct batch defects and rerun. If completion needs missing evidence or
architectural authority, leave canonical state unchanged and report `blocked`.

## Result

Report `mapped`, `no-material-delta`, or `blocked`. Include the selected scope,
frontier parents, created/reused children, terminal owners, next frontier,
observed edges, evidence baseline, changed Spine-relative paths, and checker
result. Explicitly state that depth advances by exactly one layer and that deeper
frontier was not expanded.
