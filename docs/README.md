# SpecSpine documentation

The documentation has one normative reference layer and a smaller explanatory
layer. When overview prose conflicts with a reference contract, the reference
contract takes precedence.

## Guides

1. [Core model](01-core-model.md) — purpose, authority, ownership, and
   non-goals.
2. [Usage and lifecycle](02-usage-and-lifecycle.md) — tool-independent use and
   the Doctor, Extract, Evolve, Map, and Verify lifecycle.
3. [Acceptance and reconstruction](03-acceptance-and-reconstruction.md) —
   completeness, inspection, validation, readiness, reconstruction, and
   conformance.
4. [Development and maintenance](08-development.md) — repository organization,
   validation, evaluation, and contribution guidance.

Guides explain the model and recommended workflow without duplicating every
format rule.

## Normative reference

- [Format](reference/format.md) — root and manifest shape, indexes, documents,
  sections, identifiers, assets, evidence, relationships, and reachability.
- [Glossary](reference/glossary.md) — generated index of every reserved
  identifier family, token, document kind, and enumerated format value.
- [Semantics](reference/semantics.md) — authority, statement kinds, conflicts,
  reconstruction meaning, identity, and artifact boundaries.
- [Retrieval](reference/retrieval.md) — query input, deterministic closure,
  budgets, status, omissions, and handoff output.
- [Manifest JSON Schema](../shared/references/specspine.schema.json) — portable
  machine-readable manifest shape.

The reference documents and schema define SpecSpine v4 together. The terms
**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** express
requirement levels; violating a `SHOULD` requires an explicit reason.

Canonical project specifications and their registered normative assets remain
the source of accepted project intent. Generated graphs, reports, views, and
handoffs are derived. `_INDEX.md` is deterministically regenerable but remains
the required committed entry point.
