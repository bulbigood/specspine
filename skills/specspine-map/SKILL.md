---
name: specspine-map
description: "Map observed brownfield repository architecture into a linked Markdown SpecSpine. Use bounded mode for surveys, overviews, selected subsystems, local refresh, and drift. Use exhaustive mode when the operator asks to cover the whole project: mechanically queue every production work unit, dispatch each verification ToDo to one fresh producer, integrate results centrally, and continue until the inventory is verified. Do not invent intended architecture, perform general integrity audits, implement changes, or claim code/spec conformance."
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
- Read [references/campaign-selection.md](references/campaign-selection.md)
  before starting or resuming an exhaustive campaign in a new session.
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
per bounded ToDo, one checkpoint, then termination. Use the platform's
medium-capability general-purpose agent tier for every producer: neither its
weak/cheap tier nor its strongest/premium tier. In Codex this is
`agent_type: medium`.

Treat exhaustive intent as one durable campaign, not one turn. A turn boundary,
elapsed-time boundary, context compaction, or progress report is never a
terminal condition. Before any final answer, run `campaign.py next-action` on
the exact ledger. Emit a final answer only when it returns `may_finish: true`;
otherwise perform the returned action and continue. Send intermediate counts
only as commentary, never as a final answer.

Start each producer in a fresh isolated context with no inherited conversation,
reasoning, or hidden memory. In Codex this is `fork_turns: none`; on another
agent platform use its equivalent new-session/no-history option. Pass only a
minimal command naming the producer contract, task packet, and required paths.
Dispatch strict waves in one assistant action. While a wave runs, read-only harvest completed handoffs; stop only at a predeclared timeout or explicit stall.
Publish and integrate only after the terminal barrier; never refill mid-wave.
Never reuse a producer. If the platform cannot provide both a fresh producer
and a medium-capability tier, preserve the generated ToDo and report `blocked`;
do not substitute another tier, classify production units, or simulate
exhaustive coverage in root.

Require every producer to iterate in its durable private work package, run the
specified `producer_finalize.py` preflight, and atomically expose exactly one
checked handoff package. Root independently repeats acceptance checks. Do not
invoke Doctor inside producers; its whole-Spine semantic audit is a separate
operator-authorized workflow.

If the Spine already contains specification nodes, also read
[references/documentation-first-seeding.md](references/documentation-first-seeding.md)
completely and record the mechanical documentation index before inspecting
production source.

Read [references/integration-pass.md](references/integration-pass.md)
completely before merging producer publications into the final graph.
