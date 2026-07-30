# Specification name

**ID:** `stable-document-id` · **Kind:** `subsystem`

**Summary:** Summarize the concept in one short sentence.

## Responsibility

For a new Map owner, state that this document records evidence about one
observed candidate boundary and name its apparent responsibility.

## Boundaries

Preserve accepted boundary prose for an existing owner. For a new owner, keep
code-derived boundary facts in `Observed`.

## Behavior

Preserve accepted durable behavior from the existing Spine. Map MUST NOT fill
this section from repository evidence alone.

## Relationships

Preserve this section exactly when updating an existing owner. Omit it from a
new observation-only owner: repository-derived interactions remain `OBS`,
uncertainty, or Map runtime planning data until Evolve accepts them.

Place accepted claim sections after `Relationships`, then `Known divergences`
before `Observed`, `Inferred`, and `Open questions`. Put implementation
navigation and contextual sections last. Do not wrap canonical sections in
HTML `<details>`; derived renderers may collapse supplementary content.

Add a focused Mermaid diagram when readers would otherwise have to reconstruct
a non-trivial topology, interaction, lifecycle, or data relationship. Add
`Interfaces`, `Information model`, `Data ownership`, `Lifecycle and
invariants`, `Failure behavior`, `Edge cases`, `Decisions`, `Constraints`,
`Observed`, `Inferred`, `Known divergences`, or `Open questions` only when
useful. Retain `Observed` only for boundary-significant intent gaps,
divergences, unresolved questions, or surprising navigation; do not mirror
matching intent or private implementation detail. Report independently owned
behavior or cross-cutting policy as a deferred lead; do not create a sibling
owner in the same Map invocation. Do not copy a feature-SDD outline or create
empty sections.
