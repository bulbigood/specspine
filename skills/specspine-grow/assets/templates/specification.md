# Specification name

**ID:** `stable-document-id` · **Kind:** `subsystem`

Summarize the concept in one or two sentences.

## Responsibility

Describe what this concept owns and why it exists.

## Boundaries

Describe what belongs to this concept and what belongs elsewhere. Link to the
canonical specifications for neighboring responsibilities.

## Behavior

Describe significant externally observable or architecturally relevant
behavior, including important failure or edge behavior.

For a reconstructable owner, add only applicable normative sections:

- `Requirements` (`REQ-*`) for durable system outcomes;
- `Guarantees` (`GUA-*`) for observable promises;
- `Invariants` (`INV-*`) for truths across valid states and transitions;
- `Quality constraints` (`QLT-*`) for measurable non-functional limits;
- `Verification` (`VER-*`) for durable black-box conformance.

Link exact OpenAPI, Protobuf, JSON Schema, CUE, scenario, or fixture assets
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
feature-SDD outline or create empty sections.
