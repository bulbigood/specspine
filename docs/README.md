# SpecSpine v3 documentation

This directory contains the normative SpecSpine v3 storage and retrieval
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
5. [Completeness, validation, and views](05-completeness-validation-views.md) —
   manifest facets, checks, semantic review, views, and degradation.
6. [Tooling and acceptance](06-tooling-and-acceptance.md) — derived data,
   component responsibilities, acceptance criteria, and delivery boundaries.
7. [Installation and usage](07-installation-and-usage.md) — runtime skills,
   installation, connection, mapping, growth, retrieval, and health checks.
8. [Development and maintenance](08-development.md) — repository organization,
   local validation, evaluation, integrations, and contribution guidance.
9. [Reconstruction specifications](09-reconstruction-specifications.md) —
   normative closure, specification assets, readiness, promotion, and blind
   reconstruction evaluation.

## Normative language

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to
be interpreted as requirement levels. A `SHOULD` may be violated only for an
explicit reason.

The documents in this directory define the contract together. If overview text
in the repository conflicts with these documents, this contract takes
precedence. Canonical Markdown and its owned machine-readable contract assets
remain the source of a project's accepted durable system specification;
generated indexes, graphs, reports, and handoffs are derived artifacts.
