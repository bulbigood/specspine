---
name: specspine-map
description: Map one bounded, owner-relative increment between brownfield repository evidence and accepted SpecSpine intent. Use for a focused initial survey, deepening, refresh, or drift inspection of one existing owner or one missing responsibility. Inspect one semantic frontier, retain only material observations, divergences, inferences, and open questions, update bounded inspection coverage, and verify one coherent Spine write batch. Do not recursively map adjacent areas, orchestrate repository-wide campaigns, change accepted intent or topology, implement code, or claim code/spec conformance.
---

# SpecSpine Map

Compare one bounded repository responsibility with accepted SpecSpine intent:

```text
scope → context → inspect → classify → write → verify
```

Run the workflow directly in the current agent. Do not create campaign state,
delegate phases, or recursively pursue adjacent responsibilities. One invocation
may change at most one non-index content owner plus its deterministic index and
manifest bookkeeping.

Repository evidence establishes `OBS`, not accepted intent. Preserve uncertainty
and code/spec disagreement; never infer decisions, constraints, requirements,
guarantees, relationships, or conformance.

An `OBS` is an exception layer, not a code mirror. Retain one only for a
boundary-significant intent gap, confirmed divergence, unresolved question, or
surprising owner or boundary. Evidence already represented by accepted intent
is `covered-by-intent`: update inspection coverage without duplicating it.

## Required resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims or disagreement.
- Read [references/spec-format.md](references/spec-format.md) before changing
  specifications or the manifest.
- Use [references/spec-glossary.md](references/spec-glossary.md) for reserved
  identifiers, tokens, kinds, relations, and manifest values.
- Read [references/mapping-method.md](references/mapping-method.md) before
  repository inspection.
- Read `specspine.json.presentation` before producing Markdown and preserve its
  configured headings and order.
- Start a new content owner from `assets/templates/specification.md`.
- Use only the bundled `bootstrap_spine.py`, `rebuild_indexes.py`, and
  `check_spine.py` scripts for deterministic writes and validation.

## Authority

Use repository files only as evidence of current implementation. Existing
SpecSpine intent remains authoritative as intent even when code disagrees.

Map may:

- add, update, or remove repository-backed `OBS` and `INF`;
- add or preserve an `OQ` exposed by repository uncertainty;
- record a confirmed code/intent disagreement under `Known divergences`;
- update the target owner's inspection record;
- create one new observation-only owner for a bounded missing responsibility.

Map must not:

- add, remove, or change accepted prose or normative claims;
- publish repository-derived `Relationships`;
- split, merge, move, rename, replace, or redistribute owners;
- change completeness facets from repository evidence;
- edit source, configuration, tests, or project documentation outside the
  resolved Spine root;
- treat absence of a retained observation as evidence of conformance.

If evidence suggests a topology or accepted-contract change, preserve the
question or report it as a deferred lead. Evolve owns that change.

## Workflow

### 1. Scope

Resolve `<spine-root>` using `references/spec-format.md`; absent explicit
configuration, use `specspine` relative to the current working directory.

Select exactly one target:

- one existing non-index owner; or
- one bounded missing responsibility that can become one observation-only owner.

Classify the inspection as `survey`, `deepen`, `refresh`, or `drift`. These
labels guide evidence selection and become `inspection.mode`; they do not create
different workflows or completion claims.

State the concrete question the inspection must answer. For a broad request,
choose the smallest useful starting responsibility and treat every independent
neighbor as a deferred lead. Do not promise whole-repository coverage.

If the Spine does not exist, bootstrap only its v4 envelope:

```text
python3 <skill>/scripts/bootstrap_spine.py <spine-root> \
  --project <stable-project-name> \
  --index-file <skill>/assets/templates/spine-index.md
```

Then continue with one bounded target. Do not pre-create a repository skeleton.

### 2. Context

Read the root index, manifest, target owner, and only the directly related
owners needed to understand its accepted boundary. Related owners are read-only.
For an empty Spine, use the scoped question instead of exploring for a complete
system decomposition.

Capture the target document and manifest entry before editing so the final diff
can prove that accepted meaning and completeness were preserved.

### 3. Inspect

Inspect one owner-relative semantic frontier. Read only enough representative
repository evidence to resolve applicable boundary behavior, interfaces, data
authority, controls, lifecycle, failures, and navigation.

Direct neighbor evidence may be read when required to understand the target
boundary. Do not begin mapping that neighbor. Record every independently useful
adjacent responsibility as a deferred lead for the final report.

Stop when the target boundary is understood well enough to classify the
inspected facts. Do not continue for file coverage, private mechanics, or a
recursive completeness claim.

### 4. Classify

Disposition each significant fact as exactly one of:

- `covered-by-intent`;
- `implementation-freedom`;
- `retain-observation`;
- `retain-divergence`;
- `retain-inference`;
- `retain-open-question`;
- `implementation-detail`.

Apply the replacement test from `mapping-method.md`. Only retained dispositions
produce Markdown evidence. If ownership is ambiguous or accepted intent is
required, do not choose silently; preserve an `OQ` when it belongs to the target
or return `blocked`.

### 5. Write

Apply the smallest coherent batch to the target owner and `specspine.json`.

For an existing owner:

- preserve title, ID, kind, summary, accepted prose, normative claims,
  relationships, path, and completeness facets;
- update only repository evidence, uncertainty, divergences, and inspection.

For a new observation-only owner:

- describe `Responsibility` explicitly as an observed candidate boundary;
- keep repository-derived boundary meaning under `Observed` or `Inferred`;
- omit `Relationships` and all normative sections;
- register every completeness facet as `missing`.

Use one evidence baseline near the first `Observed` section and cite a small set
of complete repository-relative paths. Update `inspection.facets` to `checked`
only for facets actually inspected in this invocation; use `not-checked` for
the rest. Inspection never raises completeness.

If a new owner was created, rebuild indexes:

```text
python3 <skill>/scripts/rebuild_indexes.py <spine-root>
```

Never edit `_INDEX.md` manually.

### 6. Verify

Review the complete target and manifest diff. Confirm:

- no second content owner changed;
- accepted meaning, relationships, paths, and completeness were preserved;
- every retained repository claim has representative evidence;
- inspection coverage matches the files and facets actually inspected;
- no recursive lead was pursued or encoded as a task queue;
- no wording implies conformance or scope completeness.

Run the mandatory whole-Spine gate:

```text
python3 <skill>/scripts/check_spine.py <spine-root>
```

Correct defects caused by the batch and rerun it. If a pre-existing failure or
missing architectural authority prevents a clean result, stop and report
`blocked`; do not broaden the operation.

## Result

Report exactly one outcome:

- `mapped` when the target documentation or inspection record changed;
- `no-material-delta` when inspected evidence required no Spine change;
- `blocked` when ownership or accepted intent requires operator or Evolve input.

Report the target owner, inspection mode and baseline, representative evidence,
changed Spine-relative paths, checker result, unresolved uncertainty, and
deferred leads. Deferred leads do not make a completed one-step operation
incomplete and must not be pursued in the same invocation.
