---
name: specspine-map
description: "Map observed brownfield repository architecture into a linked Markdown SpecSpine. Use bounded mode for surveys, overviews, selected subsystems, local refresh, and drift. Use exhaustive mode when the operator asks to cover the whole project: build a deterministic source inventory, dispatch each bounded ToDo to one fresh producer, integrate staged drafts centrally, and continue until the inventory closes. Do not invent intended architecture, perform general integrity audits, implement changes, or claim code/spec conformance."
---

# SpecSpine Map

All published nodes use stable document IDs and core or `x-*` kinds. Publish
architectural edges only through canonical `Relation | Target | Meaning`
tables; ordinary links remain navigation. Maintain qualitative
`Mapped / Partially mapped / Unmapped` coverage. Repository facts are `OBS`,
not accepted intent. Record a confirmed intent/code conflict as an evidence-
backed observation plus one `Known divergences` row; never infer or silently
resolve accepted intent. Use arc42 and ICOM only as diagnostic lenses.

Select one execution mode before project discovery:

- Use **bounded mode** for an explicitly limited operation such as a survey,
  overview, high-level map, first pass, selected concern, refresh, or drift
  recording. Repository size or the word “deep” alone does not authorize
  exhaustive orchestration.
- Use **exhaustive mode** for completion intent such as “continue until
  saturated”, “fully map every useful branch”, “cover/document this whole
  project”, or an unambiguous equivalent. A completion verb applied to the
  entire repository is explicit exhaustive intent even without words such as
  “exhaustive”, “recursive”, or “saturated”.

## Resources

- Read [references/bounded-mode.md](references/bounded-mode.md) completely for
  both modes. It is the sole mapping operation contract.
- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims or recording code/spec disagreement.
- Read [references/spec-format.md](references/spec-format.md) before creating,
  editing, or restructuring specifications.
- Read [references/mapping-method.md](references/mapping-method.md) before a
  substantial survey, refresh, or restructuring.
- Start new files from `assets/templates/` and omit empty sections.

If the live root lacks `README.md` and no separate output root exists, create a
minimal v2 index from the architecture-index template before discovery.
Otherwise keep the live root read-only and stop for setup.

## Bounded mode

Perform exactly one bounded mapping operation and stop at its reported
continuation or terminal refusal. Do not load exhaustive orchestration
instructions, create a frontier ledger, or start producers.

## Exhaustive mode

Explicit exhaustive intent approves repeated documentation writes and final
navigation normalization. It does not authorize changing accepted intent or
choosing among materially different canonical owners.

Read [references/orchestration.md](references/orchestration.md) completely
before discovery. Exhaustive mode requires fresh producer handles: one producer
per bounded ToDo, one checkpoint, then termination. Never reuse a producer or
continue its hidden conversation state. If fresh producers are unavailable,
record the deterministic inventory and report `blocked`; do not simulate
exhaustive coverage in the root context.

If the Spine already contains specification nodes, also read
[references/documentation-first-seeding.md](references/documentation-first-seeding.md)
completely and build the initial frontier from documentation gaps before
inspecting production source.

Read [references/integration-pass.md](references/integration-pass.md)
completely before merging producer publications into the final graph.
