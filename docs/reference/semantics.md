# Specspine semantics

Specifications express durable, boundary-relevant intent. They do not mirror
source layout or private algorithms.

## Authority

- `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, and `VER` are normative.
- `OBS` is confirmed implementation evidence, not accepted intent.
- `INF` is an explicitly unconfirmed interpretation.
- `OQ` is unresolved. An OQ blocks readiness only when its ID appears in the
  same document's `blockers` frontmatter.

## Ownership and relationships

One IWE document owns each architectural concept. A standalone link declares
that the target is structurally included by the source. An inline link declares
a reference. IWE derives parents, children, references, backlinks, and graph
walks from those placements.

Relationship prose must explain the architectural consequence. Specspine does
not assign a second machine relationship token because that would duplicate the
IWE graph.

## Readiness

`blocked`: `blockers` is nonempty.

`ready`: blockers are empty and all facets are `complete` or
`not-applicable`.

`incomplete`: neither blocked nor ready.
