# SpecSpine v3 glossary

This file is generated from the canonical
[`shared/references/vocabulary.json`](../../shared/references/vocabulary.json).
The JSON vocabulary owns tokens, identifier families, and enumerated values;
the format and semantics references own their normative usage.

## Identifiers and reserved paths

| Name | Syntax or value | Meaning |
|---|---|---|
| Document ID | `^[a-z0-9]+(?:-[a-z0-9]+)*$` | Stable globally unique document identity. |
| Semantic ID | `^(DEC&#124;CON&#124;REQ&#124;GUA&#124;INV&#124;QLT&#124;VER&#124;OBS&#124;INF&#124;OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$` | Stable globally unique addressable statement identity. |
| Extension token | `x-[a-z0-9]+(?:-[a-z0-9]+)*` | Project-specific document kind or relation. |
| Root index | `_INDEX.md` | Deterministic physical navigation entry point. |
| Manifest | `specspine.json` | Completeness, blockers, inspection, freedom, and asset registry. |

## Semantic identifier families

| Prefix | Canonical section | Meaning | Authority |
|---|---|---|---|
| `DEC` | `decisions` | Accepted architectural decision. | normative |
| `CON` | `constraints` | Accepted constraint on valid implementations. | normative |
| `REQ` | `requirements` | Accepted durable required outcome. | normative |
| `GUA` | `guarantees` | Accepted externally observable promise. | normative |
| `INV` | `invariants` | Truth that holds across all valid states and transitions. | normative |
| `QLT` | `quality-constraints` | Measurable non-functional constraint. | normative |
| `VER` | `verification` | Implementation-independent conformance criterion. | normative |
| `OBS` | `observed` | Confirmed architecture-significant repository evidence; not intent. | non-normative |
| `INF` | `inferred` | Explicitly unconfirmed interpretation; not intent. | non-normative |
| `OQ` | `open-questions` | Unresolved choice; it blocks reconstruction only when listed in manifest blockers. | non-normative |

## Document kinds

- `index` — Deterministic physical navigation; never owns project claims.
- `system` — A whole system boundary.
- `subsystem` — A major independently owned part of a system.
- `component` — A stable architectural unit with a distinct responsibility.
- `capability` — A durable system ability spanning one or more units.
- `behavior` — Externally significant behavior or coordination.
- `interface` — An API, command, event, port, protocol, or integration boundary.
- `data` — A durable information model or data-ownership boundary.
- `policy` — A durable rule governing system behavior.
- `deployment` — A runtime, delivery, or operational topology boundary.
- `concept` — A stable architectural concept that does not fit a narrower core kind.

Project-specific kinds use `x-*`. Statement kinds are not document kinds.

## Manifest vocabulary

### Facets

| Token | Meaning |
|---|---|
| `architecture` | Responsibilities, boundaries, decomposition, and relationships. |
| `behavior` | Externally significant outcomes and coordination. |
| `interfaces` | APIs, commands, events, ports, protocols, and contracts. |
| `data` | Information models, ownership, mutation, and consistency. |
| `failure` | Errors, retry, degradation, compensation, and recovery. |
| `quality` | Measurable non-functional constraints. |
| `verification` | Implementation-independent conformance criteria. |

### Facet values

| Token | Meaning |
|---|---|
| `complete` | The owner declares the facet sufficiently specified. |
| `partial` | Some durable information is present but a known completeness gap remains. |
| `missing` | Applicable durable information is absent. |
| `not-applicable` | The facet has been reviewed and does not apply. |

### Inspection modes

| Token | Meaning |
|---|---|
| `survey` | Broad initial repository inspection. |
| `deepen` | Deeper inspection of selected areas. |
| `refresh` | Refresh against a newer evidence baseline. |
| `drift` | Inspection focused on repository/specification drift. |
| `exhaustive` | Exhaustive inspection of the declared scope. |

### Inspection facet values

| Token | Meaning |
|---|---|
| `checked` | The facet was inspected at the recorded baseline. |
| `not-checked` | No current comparison claim is made for the facet. |

### Implementation freedom

| Token | Meaning |
|---|---|
| `contract-equivalent` | Any internals satisfying normative contracts are permitted. |
| `architecture-constrained` | Specified component boundaries and interactions are also required. |
| `exact` | Choices explicitly declared exact are required. |

### Computed statuses

| Token | Meaning |
|---|---|
| `blocked` | At least one manifest blocker is present. |
| `ready` | No blocker exists and every facet is complete or not-applicable. |
| `incomplete` | The area is neither blocked nor ready. |

### Asset roles

| Token | Meaning |
|---|---|
| `interface-contract` | Machine-readable interface contract. |
| `data-schema` | Machine-readable data schema. |
| `execution-contract` | Exact reconstruction-critical toolchain or execution contract. |
| `scenario` | Implementation-independent conformance scenario. |
| `fixture` | Normative conformance fixture. |
| `verification` | Verification asset. |


## Core relations

- `contains` — Source contains the target architectural concept.
- `decomposes-into` — Source is decomposed into the target.
- `performs` — Source performs the target behavior.
- `depends-on` — Source depends on the target.
- `exposes` — Source exposes the target interface.
- `consumes` — Source consumes the target interface or event.
- `publishes` — Source publishes the target event or contract.
- `reads-from` — Source reads data from the target.
- `writes-to` — Source writes data to the target.
- `owns-data` — Source owns the target data.
- `constrained-by` — Source is constrained by the target claim or owner.
- `implemented-by` — Source intent is currently implemented by the target evidence.
- `has-evidence` — Source claim has the target evidence.
- `superseded-by` — Source identity or claim is replaced by the target.
- `related-to` — Source has a durable relationship for which no narrower relation applies.
- `refines` — Source adds detail to the target.
- `satisfies` — Source satisfies the target requirement or constraint.
- `verified-by` — Source is verified by the target.
- `specified-by` — Source is specified by the target contract or owner.
- `compatible-with` — Source is declared compatible with the target.
- `migrates-from` — Source is the migration successor of the target.

Project-specific relations use `x-*`.

## Canonical section keys

- `responsibility` — default rendering: “Responsibility”.
- `boundaries` — default rendering: “Boundaries”.
- `behavior` — default rendering: “Behavior”.
- `interfaces` — default rendering: “Interfaces”.
- `information-model` — default rendering: “Information model”.
- `data-ownership` — default rendering: “Data ownership”.
- `lifecycle-and-invariants` — default rendering: “Lifecycle and invariants”.
- `failure-behavior` — default rendering: “Failure behavior”.
- `edge-cases` — default rendering: “Edge cases”.
- `configuration-contract` — default rendering: “Configuration contract”.
- `compatibility` — default rendering: “Compatibility”.
- `relationships` — default rendering: “Relationships”.
- `requirements` — default rendering: “Requirements”.
- `guarantees` — default rendering: “Guarantees”.
- `invariants` — default rendering: “Invariants”.
- `quality-constraints` — default rendering: “Quality constraints”.
- `verification` — default rendering: “Verification”.
- `decisions` — default rendering: “Decisions”.
- `constraints` — default rendering: “Constraints”.
- `known-divergences` — default rendering: “Known divergences”.
- `observed` — default rendering: “Observed”.
- `inferred` — default rendering: “Inferred”.
- `open-questions` — default rendering: “Open questions”.
- `implementation` — default rendering: “Implementation”.
- `risks` — default rendering: “Risks”.
- `rationale-and-trade-offs` — default rendering: “Rationale and trade-offs”.
- `terminology` — default rendering: “Terminology”.

Presentation profiles may translate rendered headings but never these keys.

## Reserved markers

| Purpose | Marker |
|---|---|
| Semantic definitions | `<!-- specspine:semantic-ids:begin --> … <!-- specspine:semantic-ids:end -->` |
| Evidence baseline | `<!-- specspine:evidence-baseline source=<source>; inspected=<YYYY-MM-DD> -->` |
| Project instruction connection | `<!-- specspine:begin --> … <!-- specspine:end -->` |
| Optional project README link | `<!-- specspine:readme:begin --> … <!-- specspine:readme:end -->` |
