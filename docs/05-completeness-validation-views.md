# Completeness, validation, and views

## Completeness

`specspine.json` is the only machine authority for area completeness. Each
non-index owner has seven facets and explicit blocking question IDs. Status is
derived as `ready`, `incomplete`, or `blocked`; it is never authored twice.

Facet completeness is a specification claim, not proof that current code
conforms. Production discovery progress belongs to Map campaign state, not the
canonical Spine.

`complete` requires semantic support in the owner or its registered assets.
The checker can reject unsupported verification and warn when other complete
facets lack conventional machine-resolvable support. Doctor reviews translated
headings, prose-only support, applicability, and actual completeness.

## Mechanical validation

Errors include malformed manifests, missing area profiles, invalid facets,
unknown blockers, asset registry defects, unsupported complete verification,
invalid identities, unresolved links, malformed relationships or divergences,
and unreachable documents. Missing conventional support for other complete
facets is a warning requiring semantic review.

Mechanical PASS means only that deterministic format invariants hold.

## Semantic review

Review checks ownership, accepted authority, completeness evidence, blocking
scope, conformance strength, decomposition, and known drift. An area marked
`ready` remains a claim until blind reconstruction and an independent
conformance suite demonstrate it.

## Views

Mermaid may clarify meaning, but prose, tables, and registered assets retain
all normative content. Derived C4, arc42, dependency graphs, backlinks,
databases, embeddings, and reports are disposable and rebuildable.
