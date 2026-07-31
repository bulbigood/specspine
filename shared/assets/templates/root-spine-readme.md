# {project} architecture

SpecSpine is the project's long-lived, linked specification and architectural memory used to reconstruct contract-equivalent implementations.

This directory contains the project's long-lived architectural intent and architecture-relevant repository observations.

## How to use this Spine

- Start with `Contents`, then follow links to the canonical owner of the area relevant to the task. Preserve stable document IDs when files move.
- SpecSpine owns accepted durable intent; source code owns the current implementation. Neither alone proves that implementation conforms to intent.
- `specspine.json` records areas, completeness, inspection coverage, blockers, and registered contract or verification assets.
- `Known divergences` links accepted intent to conflicting observations. Do not silently turn code, `OBS`, or `INF` into accepted intent.
- Update the canonical owner instead of copying a claim into another document; preserve unresolved conflicts and blocking questions explicitly.

## SpecSpine glossary

### Identifiers and extensions

- `document ID` — Stable document identity matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`.
- `semantic ID` — Addressable statement identity matching `^(?:DEC|CON|REQ|GUA|INV|QLT|VER|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$`.
- `x-*` — Project-specific document kind or relation.

### Semantic ID prefixes

- `DEC` — Accepted architectural decision.
- `CON` — Accepted constraint on valid implementations.
- `REQ` — Accepted durable required outcome.
- `GUA` — Accepted externally observable promise.
- `INV` — Truth that holds across all valid states and transitions.
- `QLT` — Measurable non-functional constraint.
- `VER` — Implementation-independent conformance criterion.
- `OBS` — Confirmed boundary-significant repository evidence; not intent.
- `INF` — Explicitly unconfirmed interpretation; not intent.
- `OQ` — Unresolved choice; it blocks reconstruction only when listed in manifest blockers.

### Document kinds

- `index` — Deterministic physical navigation; never owns project claims.
- `system` — A whole system boundary.
- `subsystem` — A major independently owned part of a system.
- `component` — A stable owner with a distinct responsibility and boundary contract.
- `capability` — A durable system ability spanning one or more units.
- `behavior` — Externally significant behavior or coordination.
- `interface` — An API, command, event, port, protocol, or integration boundary.
- `data` — A durable information model or data-ownership boundary.
- `policy` — A durable rule governing system behavior.
- `deployment` — A runtime, delivery, or operational topology boundary.
- `concept` — A stable architectural concept that does not fit a narrower core kind.

### Canonical section keys

- `responsibility` — Canonical boundary ownership and purpose.
- `boundaries` — What the owner accepts, emits, controls, owns, and delegates elsewhere.
- `behavior` — Owner-relative observable outcomes and coordination.
- `interfaces` — Boundary inputs, outputs, APIs, commands, events, ports, protocols, and contract links.
- `information-model` — Durable entities, values, and relationships.
- `data-ownership` — Creation, mutation, reading, and consistency authority.
- `lifecycle-and-invariants` — Boundary-visible states, transitions, and durable truths.
- `failure-behavior` — Boundary-visible errors, retry, degradation, compensation, and recovery.
- `edge-cases` — Architecture-significant boundary conditions.
- `configuration-contract` — Settings, defaults, precedence, validation, and reload behavior.
- `compatibility` — Versioning, interoperability, deprecation, and evolution.
- `relationships` — Typed directed links to other canonical owners or claims.
- `requirements` — Accepted durable required outcomes.
- `guarantees` — Accepted externally observable promises.
- `invariants` — Truths across all valid states and transitions.
- `quality-constraints` — Measurable non-functional requirements.
- `verification` — Implementation-independent conformance criteria.
- `decisions` — Accepted architectural choices.
- `constraints` — Accepted limits on valid implementations.
- `known-divergences` — Confirmed conflicts between accepted intent and observations.
- `observed` — Confirmed boundary-significant repository evidence.
- `inferred` — Explicitly unconfirmed interpretation.
- `open-questions` — Unresolved architectural choices.
- `implementation` — Non-normative representative repository-relative navigation anchors; never a source walkthrough.
- `risks` — Durable architecture-relevant risks.
- `rationale-and-trade-offs` — Reasons and consequences behind accepted choices.
- `terminology` — Project-specific domain terms and exact meanings.

### Relations

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

### Facets

- `architecture` — Owner responsibility, boundary, decomposition, relationships, and explicit architecture constraints.
- `behavior` — Owner-relative observable outcomes and coordination.
- `interfaces` — Inputs, outputs, APIs, commands, events, ports, protocols, and contracts crossing the owner boundary.
- `data` — Boundary information models, data authority, mutation rights, and consistency promises.
- `failure` — Boundary-visible errors, retry, degradation, compensation, and recovery.
- `quality` — Measurable boundary qualities.
- `verification` — Implementation-independent conformance criteria.

### Facet values

- `complete` — The owner declares the facet sufficiently specified.
- `partial` — Some durable information is present but a known completeness gap remains.
- `missing` — Applicable durable information is absent.
- `not-applicable` — The facet has been reviewed and does not apply.

### Inspection modes

- `survey` — Broad initial repository inspection.
- `deepen` — Deeper inspection of selected areas.
- `refresh` — Refresh against a newer evidence baseline.
- `drift` — Inspection focused on repository/specification drift.

### Inspection facet values

- `checked` — The facet was inspected at the recorded baseline.
- `not-checked` — No current comparison claim is made for the facet.

### Implementation freedom

- `contract-equivalent` — Any internals satisfying normative contracts are permitted.
- `architecture-constrained` — Explicitly accepted owner boundaries, interactions, topology, and mechanisms are also required.

### Computed statuses

- `blocked` — At least one manifest blocker is present.
- `ready` — No blocker exists and every facet is complete or not-applicable.
- `incomplete` — The area is neither blocked nor ready.

### Asset roles

- `interface-contract` — Machine-readable interface contract.
- `data-schema` — Machine-readable boundary data schema.
- `scenario` — Implementation-independent conformance scenario.
- `fixture` — Normative conformance fixture.
- `verification` — Verification asset.

### Manifest fields

- `specspine` — Stored format major; exactly 4 for this contract.
- `project` — Stable nonempty project name.
- `implementation_freedom` — Whether explicit architecture constraints supplement boundary-contract equivalence.
- `areas` — Completeness and inspection records for non-index document owners.
- `assets` — Complete registry of non-Markdown files inside the Spine.
- `presentation` — Optional language, heading, order, and index rendering profile.
- `mapping` — Optional non-normative repository mapping frontier and observed owner graph.
- `frontier` — Ordered candidate owners available for one-step Map expansion.
- `observed_edges` — Repository-observed owner edges backed by canonical OBS statements.
- `from_owner` — Existing mapped owner that exposed a frontier candidate.
- `title` — Human-readable candidate-owner title.
- `question` — Concrete boundary question for a future mapping step.
- `reason` — Why the candidate appears independently useful.
- `seed_paths` — Representative repository-relative starting paths for a frontier candidate.
- `source_owner` — Observed interaction source owner.
- `target_owner` — Observed interaction target owner.
- `observation` — OBS identifier owning an observed edge's meaning and evidence.
- `owner` — Canonical non-index document ID.
- `facets` — Completeness or inspection values by architectural facet.
- `blockers` — Globally unique blocking OQ identifiers.
- `inspection` — Repository comparison coverage at one evidence baseline.
- `source` — Identifier of the inspected repository state.
- `inspected` — ISO date of repository inspection.
- `mode` — Repository inspection mode.
- `path` — Unique Spine-root-relative asset path.
- `role` — Semantic role of a registered asset.
- `format` — Precise asset format identifier.
- `normative` — Whether conformance depends on the asset.
- `verifies` — VER identifiers verified by the asset.
- `profile` — Presentation profile version; exactly 1.
- `language` — BCP 47-style documentation language tag.
- `headings` — Localized renderings keyed by canonical section key.
- `section_order` — Every canonical section key exactly once in rendering order.
- `index` — Localized deterministic root-index text.
- `root-title` — Root index H1 template containing {project} exactly once.
- `purpose` — Portable explanation of what SpecSpine is.
- `scope` — Portable explanation of what the Spine directory contains.
- `guide-heading` — Rendered heading for root-index reading instructions.
- `guide` — Compact portable reading and authority instructions.
- `glossary-heading` — Rendered heading for the complete concise vocabulary.
- `glossary` — Complete concise localized vocabulary; it must preserve token coverage.
- `contents-heading` — Rendered heading for deterministic physical contents.
- `nested-heading` — Rendered heading for nested independent Spine roots.
- `empty` — Rendered text used when an index has no entries.

### Markdown fields and normative keywords

- `ID` — Document identity field.
- `Kind` — Document-kind field.
- `Aliases` — Optional alternate names for retrieval; never alternate identities.
- `Summary` — Required single-line document description rendered in deterministic indexes.
- `Evidence` — Repository-relative paths supporting an OBS statement.
- `Relation` — Typed relationship-table edge token.
- `Target` — Relative link to the relationship target.
- `Meaning` — Nonempty explanation of why a relationship applies.
- `Intended` — Normative semantic ID in a known-divergence row.
- `Observed` — Conflicting OBS semantic ID in a known-divergence row.
- `Consequence` — Architectural or user-visible impact of a divergence.
- `MUST` — Absolute normative requirement.
- `MUST NOT` — Absolute normative prohibition.
- `SHOULD` — Recommended normative choice; deviation requires an explicit reason.
- `SHOULD NOT` — Normally prohibited choice; deviation requires an explicit reason.
- `MAY` — Permitted optional behavior.

### Reserved markers

- `semantic-ids` — Reserved marker syntax: `<!-- specspine:semantic-ids:begin --> … <!-- specspine:semantic-ids:end -->`.
- `evidence-baseline` — Reserved marker syntax: `<!-- specspine:evidence-baseline source=<source>; inspected=<YYYY-MM-DD> -->`.
- `connection` — Reserved marker syntax: `<!-- specspine:begin --> … <!-- specspine:end -->`.
- `readme` — Reserved marker syntax: `<!-- specspine:readme:begin --> … <!-- specspine:readme:end -->`.

### Reserved paths

- `_INDEX.md` — Deterministic physical navigation.
- `specspine.json` — Manifest and completeness registry.
- `README.md` — Portable SpecSpine introduction, reading guide, and vocabulary.
