# Specspine semantics

Specifications express durable, boundary-relevant intent. They do not mirror source layout or private algorithms.

## Authority

- `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, and `VER` are normative.
- An asset is normative only when its registration declares `normative: true`.
- `OBS` and non-normative assets are confirmed evidence, not accepted intent.
- `INF` is an explicitly unconfirmed interpretation.
- `OQ` is unresolved. It blocks readiness only when its ID appears in the same document's `blockers` frontmatter.

Normative verification criteria describe observable outcomes independently of private implementation choices. A conformance workflow may compare those criteria with code, tests, runtime behavior, and other evidence.

## Ownership and relationships

One IWE document owns each durable architectural concept. A link that is the only content of its paragraph declares structural inclusion. An inline link declares a reference. IWE derives graph relationships and traversal from those placements.

Relationship prose explains the architectural consequence. Specspine does not assign a second machine relationship token or maintain a parallel graph. It adopts richer relationship semantics through IWE when IWE provides them.

## Readiness

`blocked`: `blockers` contains one or more owner-local `OQ-*` IDs.

`ready`: blockers are empty, all facets are `complete` or `not-applicable`, and those declarations agree with the accepted content.

`incomplete`: neither blocked nor ready.

Schema validation establishes format conformance. Semantic validation also checks owner-local ID uniqueness, blocker targets, and honest completeness.
