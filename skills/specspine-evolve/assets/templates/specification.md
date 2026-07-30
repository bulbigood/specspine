# Specification name

**ID:** `stable-document-id` · **Kind:** `subsystem`

**Summary:** Summarize the concept in one short sentence.

## Responsibility

Describe the outcome this owner is accountable for.

## Boundaries

Describe accepted inputs, emitted outputs, controls, data authority, and what
belongs elsewhere. Link neighboring canonical owners.

## Behavior

Describe owner-relative observable outcomes, including important failure or
edge behavior. Apply the replacement test; omit private implementation.

For a reconstructable owner, add only applicable normative sections:

- `Requirements` (`REQ-*`) for durable system outcomes;
- `Guarantees` (`GUA-*`) for observable promises;
- `Invariants` (`INV-*`) for truths across valid states and transitions;
- `Quality constraints` (`QLT-*`) for measurable non-functional limits;
- `Verification` (`VER-*`) for durable black-box conformance.

Link OpenAPI, Protobuf, JSON Schema, CUE, scenario, or fixture assets
owned by this specification instead of paraphrasing their full content.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `depends-on` | [Neighbor](neighbor.md) | Explain the architectural consequence |

Store each directed typed edge once. Use prose links only for navigation and
local explanation. Omit this section when there are no useful typed edges.

Add a focused Mermaid diagram when readers would otherwise have to reconstruct
a non-trivial topology, interaction, lifecycle, or data relationship. Add
`Interfaces`, `Information model`, `Data ownership`, `Lifecycle and
invariants`, `Failure behavior`, `Edge cases`, `Configuration contract`,
`Compatibility`, `Decisions`, `Constraints`, `Observed`, `Inferred`, `Known
divergences`, or `Open questions` only when useful. Promote independently owned
behavior or cross-cutting policy to its own node. Do not copy a temporary
feature-SDD outline, internal algorithm, call sequence, helper inventory, or
framework walkthrough, and do not create empty sections.
