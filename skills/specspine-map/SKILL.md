---
name: specspine-map
description: Grow repository-observed SpecSpine documentation one bounded semantic step at a time. Use for an initial brownfield survey, focused refinement, frontier expansion into one adjacent responsibility, refresh, or drift inspection. Persist candidate owners in the manifest mapping frontier, create at most one observation-only owner per invocation, connect mapped owners through OBS-backed observed edges, retain only material evidence and uncertainty, and verify one coherent write batch. Do not recursively map multiple owners, turn repository evidence into accepted Relationships or normative intent, implement code, or claim code/spec conformance.
---

# SpecSpine Map

Grow the repository-observed documentation graph through one operation:

```text
scope → select → inspect → classify → write → verify
```

Run the workflow directly in the current agent. Do not create campaign state or
delegate phases. One invocation may change at most one non-index content owner,
plus deterministic indexes and `specspine.json`.

Repository evidence establishes `OBS`, `INF`, mapping frontier, and observed
edges. It never establishes accepted intent, canonical `Relationships`, or
conformance.

An `OBS` is an exception layer, not a code mirror. Retain one only for a
boundary-significant intent gap, confirmed divergence, unresolved question,
surprising owner/boundary, or the interaction supporting an observed edge.
Evidence already represented by accepted intent is `covered-by-intent`: update
inspection coverage without duplicating it.

## Required resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims or disagreement.
- Read [references/spec-format.md](references/spec-format.md) before changing
  specifications or the manifest.
- Read [references/owner-operations.md](references/owner-operations.md) before
  selecting `refine` or `expand`, creating an owner, or changing graph shape.
- Use [references/spec-glossary.md](references/spec-glossary.md) for reserved
  identifiers, tokens, kinds, relations, and manifest fields.
- Read [references/mapping-method.md](references/mapping-method.md) before
  repository inspection.
- Read `specspine.json.presentation` before producing Markdown and preserve its
  configured headings and order.
- Start a new content owner from `assets/templates/specification.md`.
- Use only the bundled `bootstrap_spine.py`, `rebuild_indexes.py`, and
  `check_spine.py` scripts for deterministic writes and validation.

## Authority

Map may:

- add, update, or remove repository-backed `OBS` and `INF`;
- add or preserve an `OQ` exposed by repository uncertainty;
- record a confirmed code/intent disagreement under `Known divergences`;
- update the inspected owner's inspection record;
- persist adjacent candidate owners under `mapping.frontier`;
- create one new observation-only owner;
- publish an OBS-backed non-normative edge under
  `mapping.observed_edges`.

Map must not:

- add, remove, or change accepted prose or normative claims;
- publish repository-derived canonical `Relationships`;
- split, merge, move, rename, replace, or redistribute existing owners;
- change completeness facets from repository evidence;
- edit source, configuration, tests, or project documentation outside the
  resolved Spine root;
- treat absence of a retained observation as evidence of conformance.

Evolve owns accepted topology. It may later promote an observed edge into a
canonical `Relationship` after explicit acceptance.

## Manifest mapping model

Use the optional `mapping` object as durable, non-normative repository mapping
state:

```json
{
  "mapping": {
    "frontier": [
      {
        "id": "graph-rendering-engine",
        "from_owner": "time-series-visualization",
        "title": "Graph rendering engine",
        "question": "Which rendering lifecycle and data-alignment responsibility does it own?",
        "reason": "The mapped panel delegates a distinct reusable boundary.",
        "seed_paths": ["public/app/core/components/GraphNG/GraphNG.tsx"]
      }
    ],
    "observed_edges": [
      {
        "source_owner": "time-series-visualization",
        "target_owner": "graph-rendering-engine",
        "observation": "OBS-graph-rendering-delegation"
      }
    ]
  }
}
```

`frontier` is the ordered queue of independently useful candidate owners.
`observed_edges` is a machine-traversable repository graph. Each edge references
one canonical `OBS` that owns its meaning and evidence. Edge direction describes
the interaction stated by that observation, not discovery order. Neither field
is accepted architecture or delivery work.

## Workflow

### 1. Scope

Resolve `<spine-root>` using `references/spec-format.md`; absent explicit
configuration, use `specspine` relative to the current working directory.

Classify repository inspection as `survey`, `deepen`, `refresh`, or `drift`.
Separately choose one action:

- `refine`: inspect one new facet of an existing owner;
- `expand`: consume or establish one frontier lead and map that adjacent owner.

Apply the shared action and owner mechanics from `owner-operations.md`. Map
authorizes `refine` and the `create` primitive of `expand`; it does not
authorize any other structural primitive.

Choose the action deterministically:

1. Honor an explicit `refine`, named facet/question, `refresh`, or `drift`.
2. Honor an explicit `expand` or explicitly named missing responsibility.
3. For a generic request to deepen or continue documentation, select `expand`
   when the named/current owner has an applicable frontier lead; consume the
   first such lead in manifest order.
4. Otherwise select `refine`.

If the Spine does not exist, bootstrap only its v4 envelope:

```text
python3 <skill>/scripts/bootstrap_spine.py <spine-root> \
  --project <stable-project-name> \
  --index-file <skill>/assets/templates/spine-index.md
```

Then create one bounded starting owner and persist every independently useful
adjacent responsibility in `mapping.frontier`. Do not pre-create a repository
skeleton.

### 2. Select

For `refine`, select exactly one existing non-index owner.

For `expand`, select exactly one frontier entry. Its `id` becomes the new owner
ID and its `from_owner` is read-only context. Remove the entry only after the
candidate is dispositioned:

- create the owner when evidence confirms an independently useful boundary;
- remove the lead without creating an owner when evidence disproves it;
- keep the lead unchanged and return `blocked` when evidence is insufficient.

Do not choose the existing `from_owner` as the write target during expansion.
Apply the shared owner test before creating it.

### 3. Inspect

Inspect one owner-relative semantic frontier. Read only enough representative
repository evidence to resolve applicable responsibility, boundary behavior,
interfaces, data authority, controls, lifecycle, failures, and interactions.

For `refine`, stop after the selected facet is understood. Persist newly exposed
independent responsibilities in `mapping.frontier`.

For `expand`, inspect the candidate boundary and its immediate interaction with
existing owners. Persist further independent neighbors as new frontier entries,
but do not map them in the same invocation.

Stop when the selected boundary is classifiable. Do not continue for file
coverage, private mechanics, or recursive completeness.

### 4. Classify

Disposition each significant fact as exactly one of:

- `covered-by-intent`;
- `implementation-freedom`;
- `retain-observation`;
- `retain-divergence`;
- `retain-inference`;
- `retain-open-question`;
- `implementation-detail`;
- `frontier-candidate`.

Apply the replacement test from `mapping-method.md`. Only retained dispositions,
frontier entries, and OBS-backed observed edges survive.

Create a frontier entry only when the candidate appears independently useful,
is not an existing owner, and is not already present. Use a stable semantic ID,
one concrete question, a boundary reason, and a small set of seed paths.

### 5. Write

Apply one coherent batch to the selected content owner and `specspine.json`.

For `refine`:

- preserve title, ID, kind, summary, accepted prose, normative claims,
  relationships, path, and completeness facets;
- update only repository evidence, uncertainty, divergences, inspection, and
  mapping frontier/edges.

For `expand`:

- create the selected observation-only owner through the shared `expand`
  protocol;
- describe `Responsibility` as an observed candidate boundary;
- keep repository-derived boundary meaning under `Observed` or `Inferred`;
- include an `OBS` describing each retained interaction with mapped owners;
- add at least one `mapping.observed_edges` entry referencing such an `OBS`;
- omit canonical `Relationships` and all normative sections;
- register every completeness facet as `missing`;
- consume the selected frontier entry.

Use one evidence baseline near the first `Observed` section and cite a small set
of complete repository-relative paths. Update `inspection.facets` to `checked`
only for facets actually inspected; use `not-checked` for the rest.

If an owner was created, rebuild indexes:

```text
python3 <skill>/scripts/rebuild_indexes.py <spine-root>
```

Never edit `_INDEX.md` manually.

### 6. Verify

Review the complete diff. Confirm:

- no second content owner changed;
- accepted meaning, canonical relationships, paths, and completeness were
  preserved;
- every observed edge references an existing `OBS` owned by one endpoint;
- every frontier source is an existing owner and every candidate ID is unused;
- consumed leads disappeared and new leads are unique;
- every retained repository claim has representative evidence;
- inspection coverage matches the files and facets actually inspected;
- no wording implies acceptance, conformance, or scope completeness.

Run the mandatory whole-Spine gate with repository evidence validation:

```text
python3 <skill>/scripts/check_spine.py <spine-root> \
  --repository-root <repository-root>
```

Correct defects caused by the batch and rerun it. If a pre-existing failure or
missing architectural authority prevents a clean result, stop and report
`blocked`; do not broaden the operation.

## Result

Report exactly one outcome:

- `mapped` when one owner, mapping frontier, observed graph, or inspection
  record changed;
- `no-material-delta` when inspected evidence required no Spine change;
- `blocked` when ownership, evidence, or accepted intent requires input.

Report action, owner, inspection mode and baseline, representative evidence,
changed Spine-relative paths, consumed and added frontier leads, observed edges,
checker result, and unresolved uncertainty. Do not automatically perform the
next frontier step in the same invocation.
