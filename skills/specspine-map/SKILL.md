---
name: specspine-map
description: Grow repository-observed SpecSpine documentation one bounded semantic step at a time. Use for an initial brownfield survey, focused refinement, frontier expansion into one adjacent responsibility, refresh, or drift inspection. Persist candidate owners in the manifest mapping frontier, create at most one observation-only owner per invocation, connect mapped owners through OBS-backed observed edges, retain only material evidence and uncertainty, and verify one coherent write batch. Do not recursively map multiple owners, turn repository evidence into accepted Relationships or normative intent, implement code, or claim code/spec conformance.
---

# SpecSpine Map

Grow the repository-observed documentation graph through one operation:

```text
scope → select → inspect → classify → write → verify
```

Run directly in the current agent. One invocation may change at most one
non-index content owner, plus deterministic indexes and `specspine.json`.

Repository evidence establishes `OBS`, `INF`, mapping frontier, and observed
edges. It never establishes accepted intent, canonical `Relationships`,
completeness, or conformance. An `OBS` is an exception layer, not a code mirror.

## Required resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims or disagreement.
- Read [references/spec-format.md](references/spec-format.md) before changing
  specifications or the manifest.
- Read [references/owner-operations.md](references/owner-operations.md) before
  selecting `refine` or `expand` or creating an owner.
- Read [references/mapping-method.md](references/mapping-method.md) before
  repository inspection.
- Use [references/spec-glossary.md](references/spec-glossary.md) for reserved
  identifiers and manifest fields.
- Read `specspine.json.presentation` before writing Markdown.
- Start a new owner from `assets/templates/specification.md`.
- Use only bundled `bootstrap_spine.py`, `rebuild_indexes.py`, and
  `check_spine.py` for deterministic writes and validation.

## Authority

Map may:

- add, update, or remove repository-backed `OBS` and `INF`;
- retain an evidence-backed `OQ` or confirmed divergence;
- update one owner's inspection record;
- persist adjacent candidate owners under `mapping.frontier`;
- create one observation-only owner through `expand`;
- publish OBS-backed non-normative `mapping.observed_edges`.

Map must not:

- change accepted prose, normative claims, completeness, or canonical
  `Relationships`;
- publish repository-derived canonical `Relationships`;
- split, merge, move, rename, replace, or redistribute existing owners;
- change more than one content owner;
- document private implementation;
- recursively map frontier leads;
- claim code/spec conformance or scope completeness.

Evolve owns accepted topology and may later promote an observed owner or edge
after explicit acceptance. Map authorizes only shared `refine` and
`expand/create`; it authorizes no other structural primitive.

## Mapping model

`mapping.frontier` is an ordered queue of independently useful adjacent owner
candidates:

```json
{
  "id": "graph-rendering-engine",
  "anchor_owner": "time-series-visualization",
  "title": "Graph rendering engine",
  "question": "Which rendering lifecycle and data-alignment boundary does it own?",
  "reason": "The mapped panel delegates a distinct reusable responsibility.",
  "seed_paths": ["public/app/core/components/GraphNG/GraphNG.tsx"]
}
```

`anchor_owner` is the mapped owner near which the candidate was discovered. It
does not assert containment, parentage, or edge direction. Candidates may be
children, dependencies, consumers, peers, integrations, or shared authorities.

`mapping.observed_edges` is the machine-traversable repository graph. Each edge
references one canonical `OBS` owned by one endpoint. It is not an accepted
`Relationship`; Evolve may later promote an observed edge after explicit
acceptance.

## Workflow

### 1. Scope

Resolve `<spine-root>` from `spec-format.md`; otherwise use `specspine`.
Classify inspection as `survey`, `deepen`, `refresh`, or `drift`. Separately
select:

- `refine`: inspect one facet or question of one existing owner;
- `expand`: consume one frontier lead or map one explicitly named missing
  responsibility.

Choose deterministically:

1. Honor an explicit `refine`, named facet/question, `refresh`, or `drift`.
2. Honor an explicit `expand` or explicitly named missing responsibility.
3. For generic `deepen` or `continue`, select `expand` when the named/current
   owner has an applicable frontier lead; consume the first such lead in
   manifest order.
4. Otherwise select `refine`.

If the Spine is absent, bootstrap only its v4 envelope, create one bounded
starting owner, and persist adjacent candidates. Do not create their documents.

### 2. Select

For `refine`, select exactly one existing non-index write owner.

For `expand`, select exactly one frontier entry. Its `id` becomes the new owner
ID; `anchor_owner` is read-only context. Apply the shared owner test. Disposition
the lead:

- create the owner and consume the lead when evidence confirms the boundary;
- remove it without creating an owner when evidence disproves it;
- preserve it and return `blocked` when evidence is insufficient.

### 3. Inspect

Inspect one owner-relative semantic frontier. Read only enough representative
evidence to resolve the selected responsibility, boundary behavior, interfaces,
data authority, controls, lifecycle, failures, and immediate interactions.

For `refine`, stop after the selected facet is understood. For `expand`, stop
after the candidate and its interaction with mapped owners are classifiable.
Persist newly exposed independent responsibilities as frontier leads; never
map them in the same invocation.

### 4. Classify

Classify each significant fact as:

- `covered-by-intent`;
- `implementation-freedom`;
- `retain-observation`;
- `retain-divergence`;
- `retain-inference`;
- `retain-open-question`;
- `implementation-detail`;
- `frontier-candidate`.

Apply the replacement test from `mapping-method.md`. Retain only material
dispositions, frontier entries, and OBS-backed observed edges.

### 5. Write

Apply one coherent batch to the selected content owner and manifest.

For `refine`, preserve title, ID, kind, summary, responsibility, accepted
prose, normative claims, relationships, assets, path, and completeness. Update
only repository evidence, uncertainty, divergences, inspection, and mapping
state.

For `expand`:

- create exactly one observation-only owner through the shared protocol;
- describe `Responsibility` as an observed candidate boundary;
- keep repository-derived meaning under `Observed` or `Inferred`;
- include an `OBS` for each retained interaction with mapped owners;
- add at least one `mapping.observed_edges` entry referencing such an `OBS`;
- omit canonical `Relationships` and normative sections;
- register every completeness facet as `missing`;
- consume exactly the selected frontier lead.

Use one evidence baseline and a small set of complete repository-relative
paths. Record only facets actually inspected. Rebuild indexes after owner
creation; never edit `_INDEX.md` manually.

### 6. Verify

Review the complete diff. Confirm:

- at most one content owner changed;
- accepted meaning, canonical relationships, paths, and completeness were
  preserved;
- exactly one frontier lead was consumed by an expansion;
- new frontier leads were persisted but not pursued;
- every observed edge references an endpoint-owned `OBS`;
- every frontier anchor exists and every candidate ID is unused;
- evidence and inspection coverage are accurate;
- no wording implies acceptance, conformance, or scope completeness.

Run the mandatory whole-Spine gate:

```text
python3 <skill>/scripts/check_spine.py <spine-root> \
  --repository-root <repository-root>
```

Correct defects caused by the batch and rerun. Stop `blocked` when evidence or
architectural authority is insufficient; do not broaden the operation.

## Result

Report `mapped`, `no-material-delta`, or `blocked`. Include action, owner,
inspection mode and baseline, representative evidence, changed paths, consumed
and added frontier leads, observed edges, checker result, and unresolved
uncertainty. Never perform the next frontier step automatically.
