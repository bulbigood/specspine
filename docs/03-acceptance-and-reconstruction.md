# Acceptance and reconstruction

## Completeness and readiness

Each non-index owner has manifest facets for architecture, behavior,
interfaces, data, failure behavior, quality, and verification. A facet is
`complete`, `partial`, `missing`, or `not-applicable`. The owner kind determines
which facets are required.

An area is:

- `blocked` when it references unresolved blocking `OQ-*` statements;
- `incomplete` when a required facet is partial or missing;
- `ready` otherwise.

These are specification claims. They do not prove semantic completeness,
correct decomposition, impact completeness, or current-code conformance.

Inspection coverage records what repository comparison occurred, at which
source baseline and date, and which facets were checked. It never changes
readiness and never proves conformance. Absence of `OBS`, divergences, or
inspection records makes no conformance claim.

## Validation

Mechanical validation checks identity, links, statement IDs, relations,
manifest shape, evidence paths, reachability, assets, and deterministic
indexes. Semantic review evaluates ownership, boundaries, claim classification,
decomposition, and whether declared completeness is justified.

Neither validation mode decides product intent. Derived graphs, reports,
indexes, and handoffs are deterministically regenerable and never independent
editing authorities. The required `_INDEX.md` remains committed as the portable
entry point.

## Reconstruction bundle

A reconstruction bundle contains the selected owner closure, applicable
accepted claims, required neighbors, registered normative assets, declared
implementation freedom, blockers, and implementation-independent verification.
Observations may orient the work but do not become reconstruction requirements.

`implementation_freedom` controls equivalence:

- `contract-equivalent` permits any internals satisfying the normative closure;
- `architecture-constrained` also preserves specified components and
  interactions;
- `exact` preserves only implementation choices explicitly declared exact.

Undocumented source details never become exact requirements automatically.

## Conformance

Verify compares an implementation or blind reconstruction with the selected
normative closure and its independent verification surface. Code similarity is
not a goal. A successful result establishes only the checked scope and
baseline.

A blind reconstruction benchmark is the strongest test of whether a `ready`
bundle is sufficient without hidden policy invention. If an implementing agent
must invent policy, the result exposes a specification gap even when the
implementation appears reasonable.

## Acceptance criteria

SpecSpine succeeds when:

- a reader without special tooling can navigate from `_INDEX.md` and
  distinguish accepted intent, exception evidence, uncertainty, and conflict;
- the same root deterministically produces the same graph, status, assets, and
  retrieval closure;
- task retrieval finds the canonical owner, applicable claims, required
  neighbors, assets, blockers, and known divergences;
- a `ready` benchmark slice can be independently implemented without inventing
  unresolved policy and can pass its owned conformance surface;
- no workflow silently promotes `OBS` or `INF`, resolves `OQ`, or treats code as
  automatic authority over accepted intent.
