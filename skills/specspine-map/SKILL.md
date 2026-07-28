---
name: specspine-map
description: "Map observed brownfield repository architecture into a linked Markdown SpecSpine. Use bounded-step mode for surveys, overviews, local refresh, drift, or one limited deepening operation. Use an exhaustive campaign when the operator asks to completely document any scope, including a named architectural topic, related services, or the whole repository: recursively close a semantic discovery frontier, synthesize it against existing SpecSpine coverage, dispatch uncovered topics to fresh producers, and integrate until the requested scope is verified. Do not invent intended architecture, perform general integrity audits, implement changes, or claim code/spec conformance."
---

# SpecSpine Map

All published nodes use stable document IDs and core or `x-*` kinds. Publish
architectural edges only through canonical `Relation | Target | Meaning`
tables; ordinary links remain navigation. Maintain evidence-backed manifest
facets for every published owner. Repository facts are `OBS`, not accepted
intent; never turn required policy into a Map ToDo. Record conflicts as
observation plus one `Known divergences` row; never infer or silently resolve
accepted intent. Use arc42 and ICOM only as diagnostic lenses.

Select one operation before project discovery:

- Use **bounded-step mode** for an explicitly limited operation such as a survey,
  overview, high-level map, first pass, selected concern, refresh, or drift
  recording. Repository size or the word “deep” alone does not authorize
  exhaustive orchestration.
- Use an **exhaustive campaign** for completion intent applied to any scope:
  “fully document Kafka and related services”, “continue this subsystem until
  saturated”, “cover this whole project”, or an unambiguous equivalent. The
  whole repository is one exhaustive scope, not a separate campaign type.

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
- In exhaustive discovery, give each scout
  [references/discovery-task.md](references/discovery-task.md), each
  between-level curator
  [references/frontier-curation.md](references/frontier-curation.md), and the
  final synthesis agent
  [references/topic-synthesis.md](references/topic-synthesis.md).
- Start new files from `assets/templates/` and omit empty sections.

If live `README.md` is absent and no output root exists, create the root pair;
otherwise keep it read-only. Omit index progress, future work, and placeholders.
`seed-from-spine` accepts only v3; its repairable baseline must clear at finish.

## Bounded-step mode
Perform exactly one bounded mapping operation and stop at its reported
continuation or terminal refusal. Do not load exhaustive orchestration
instructions, create a frontier ledger, or start producers.

## Exhaustive campaign
Explicit exhaustive intent approves repeated documentation writes and final
navigation normalization. It does not authorize changing accepted intent or
choosing among materially different canonical owners.

Map records each owner's supported and missing manifest facets. Evidence
cannot create normative claims or produce `ready` status.

Read [references/orchestration.md](references/orchestration.md) completely
before discovery. Every exhaustive scope uses the same semantic-frontier,
synthesis, producer, and integration pipeline. A whole-repository flat
production-file inventory is only an optional discovery accelerator; it grants
no architectural grouping or completion authority. Use fresh discovery
scouts, fresh frontier curators between discovery levels, one fresh whole-corpus synthesis
agent that removes topics already covered by the current Spine, then one fresh
producer per remaining bounded semantic ToDo. Use
the platform's medium-capability general-purpose tier for every role: neither
weak/cheap nor strongest/premium. In Codex this is `agent_type: medium`.

Treat exhaustive intent as one durable campaign, not one turn. Before
`source-pass`, pause only between fully settled discovery levels with every
packet, result, and frontier decision stored under the durable run root and no
discovery agent live. After `source-pass`, run `campaign.py next-action` on the
exact ledger before any final answer. Success or blockage requires
`may_finish: true`; an unavoidable platform boundary additionally requires
`may_pause: true`. Never stop with assigned, review, or privately published
work. Send ordinary intermediate counts only as commentary.

Start each discovery, curation, synthesis, and producer agent in a fresh isolated context
(`fork_turns: none` in Codex; equivalent on another agent platform). Pass only
its phase contract, inputs, and required paths.
Dispatch strict waves of at most five producers: precompute every prompt, then emit spawn calls back-to-back with no reasoning or other tools between them; use platform batch spawn when available.
While a wave runs, read-only harvest completed handoffs; publish/integrate only after its terminal barrier, never refill, and stop only at a predeclared timeout or explicit stall.
Never reuse a producer. If the platform cannot provide both a fresh producer
and a medium-capability tier, preserve the generated ToDo and report `blocked`;
do not substitute another tier or simulate exhaustive coverage in root.

Require every producer to iterate in its durable private work package, run the
specified `producer_finalize.py` preflight, and atomically expose exactly one
checked handoff package. Root independently repeats acceptance checks. Do not
invoke Doctor inside producers; its whole-Spine semantic audit is a separate
operator-authorized workflow.

Acceptance never edits live Spine. Publish one checked private workspace and
advance the ledger together. Use `covered` only for scope verification, `answered` or
`unresolved` only for anchored questions, and disposition every anchor.

For an existing Spine, read [documentation-first-seeding.md](references/documentation-first-seeding.md)
and record its mechanical index before production source.

Read [references/integration-pass.md](references/integration-pass.md)
completely before merging producer publications into the final graph.
