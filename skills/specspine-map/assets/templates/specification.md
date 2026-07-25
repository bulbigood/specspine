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

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `depends-on` | [Neighbor](neighbor.md) | Explain the architectural consequence |

Store each directed typed edge once. Use ordinary prose links for navigation,
not as implicit relationships. Omit this section when there are no useful
typed edges.

Add a focused Mermaid diagram when readers would otherwise have to reconstruct
a non-trivial topology, interaction, lifecycle, or data relationship. Add
`Interfaces`, `Information model`, `Data ownership`, `Lifecycle and
invariants`, `Failure behavior`, `Edge cases`, `Decisions`, `Constraints`,
`Observed`, `Inferred`, `Known divergences`, or `Open questions` only when
useful. Promote independently owned behavior or cross-cutting policy to its own
node. Do not copy a feature-SDD outline or create empty sections.
