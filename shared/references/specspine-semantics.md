# Specspine semantics

Specifications express durable, boundary-relevant intent. They do not mirror source layout or private algorithms.

## Authority

- `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, and `VER` are normative.
- An asset is normative only when its registration declares `normative: true`.
- `OBS` and non-normative assets are confirmed evidence, not accepted intent.
- `INF` is an explicitly unconfirmed interpretation.
- `OQ` is unresolved. It blocks readiness only when its ID appears in the same document's `blockers` frontmatter.

Normative verification criteria describe observable outcomes independently of private implementation choices. A conformance workflow may compare those criteria with code, tests, runtime behavior, and other evidence.

`Responsibility`, `Boundaries`, `Behavior`, `Interfaces`, `Information model`, `Data ownership`, `Lifecycle and invariants`, `Failure behavior`, `Edge cases`, `Configuration contract`, and `Compatibility` carry accepted normative prose. Semantic IDs make exact claims addressable; they do not make otherwise normative boundary prose optional or turn explanatory evidence into intent. `Known divergences`, `Observed`, `Inferred`, `Open questions`, `Implementation`, `Risks`, `Rationale and trade-offs`, and `Terminology` are non-normative. A link inside them retains the target statement's authority but does not make the surrounding prose normative.

Evidence follows an exception layer. Do not persist an `OBS-*` merely to repeat behavior already fully entailed by accepted intent. Persist evidence when it records an undocumented boundary-significant fact, a divergence, or provenance that a requested inspection needs. `INF-*` is not a substitute for accepted intent. A refresh or drift inspection replaces evidence that is no longer true instead of accumulating stale current-state claims; Git retains history.

## Ownership and relationships

One IWE document owns each durable architectural concept. A link that is the only content of its paragraph declares structural inclusion. An inline link declares a reference. IWE derives graph relationships and traversal from those placements.

Refine an existing owner when a candidate responsibility is already governed by its accepted boundary. Expand the graph only when the candidate is independently useful, has a durable responsibility, lifecycle, or external boundary of its own, and is not merely a source-layout or feature subtopic. A workflow records the existing owners tested before creating a new one.

Relationship prose explains the architectural consequence. Specspine does not assign a second machine relationship token or maintain a parallel graph. It adopts richer relationship semantics through IWE when IWE provides them.

The IWE key is the owner's current canonical address. An IWE-managed rename is
an explicit address migration: accepted meaning and owner-local statement IDs
stay unchanged, managed links are rewritten, and external consumers must update
stored keys. Specspine intentionally does not maintain an immutable parallel ID.

## Readiness

`blocked`: `blockers` contains one or more owner-local `OQ-*` IDs.

`ready`: blockers are empty, all facets are `complete` or `not-applicable`, and those declarations agree with the accepted content.

`incomplete`: neither blocked nor ready.

Schema validation establishes format conformance. Semantic validation also checks owner-local ID uniqueness, blocker targets, exhaustive-boundary basis, asset targets and existence, verification support, title consistency, and honest completeness.

For a retrieved closure, implementation freedom is `architecture-constrained` when any applicable governing owner declares it; otherwise it is `contract-equivalent`. A workflow reports which owner introduced the stricter constraint and does not weaken it by aggregation.
