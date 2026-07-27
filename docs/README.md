# SpecSpine v2 documentation

This directory contains the normative SpecSpine v2 storage and retrieval
contract. The documents are split by stable responsibility so readers and
agents can load only the relevant part without reconstructing rules from one
large design document.

## Documentation map

1. [Core model](01-core-model.md) — purpose, authority, canonical ownership,
   file organization, and non-goals.
2. [Markdown format](02-markdown-format.md) — index and node shape, identity,
   sections, relationships, semantic addresses, and promotion rules.
3. [Semantics and evidence](03-semantics-and-evidence.md) — statement kinds,
   provenance, uncertainty, accepted intent, observations, and divergences.
4. [Retrieval contract](04-retrieval-contract.md) — task closure, query input,
   graph traversal, budgets, statuses, and handoff output.
5. [Coverage, validation, and views](05-coverage-validation-views.md) —
   coverage, mechanical checks, semantic review, diagrams, and degradation.
6. [Tooling, migration, and acceptance](06-tooling-migration-acceptance.md) —
   derived data, component responsibilities, migration, acceptance criteria,
   and delivery boundaries.
7. [Installation and usage](07-installation-and-usage.md) — runtime skills,
   installation, connection, mapping, growth, retrieval, and diagnosis.
8. [Development and maintenance](08-development.md) — repository organization,
   local validation, evaluation, integrations, and contribution guidance.

## Normative language

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to
be interpreted as requirement levels. A `SHOULD` may be violated only for an
explicit reason.

The documents in this directory define the contract together. If overview text
in the repository conflicts with these documents, this contract takes
precedence. Canonical Markdown inside a project remains the source of that
project's accepted architectural intent; generated indexes, graphs, reports,
and handoffs are derived artifacts.
