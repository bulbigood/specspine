# Specspine v5 glossary

This is a human-oriented index, not an additional skill contract. The linked
[format](format.md), [semantics](semantics.md),
[conformance](conformance.md), and [audit](audit.md) references remain the
authoritative definitions used by skills. Semantic ID prefixes and their
purposes are defined in the
[semantic-statements table](semantics.md#semantic-statements).

| Term                | Meaning                                                                                               |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| Owner               | One canonical specification represented by an IWE document.                                           |
| Document key        | Current canonical owner address assigned by IWE; migrated by an IWE-managed rename.                    |
| Inclusion           | Link-only paragraph; structural parent/child edge.                                                    |
| Reference           | Link inside prose; non-structural graph edge.                                                         |
| Facet               | Declared completeness of architecture, behavior, interfaces, data, failure, quality, or verification. |
| Blocker             | Owner-local `OQ-*` listed in `blockers` and preventing readiness.                                     |
| Normative statement | Accepted constraint on conforming implementations.                                                    |
| Normative asset     | Registered asset with `normative: true`; part of accepted intent.                                     |
| Observation         | Confirmed evidence that is not accepted intent.                                                       |
| Semantic readiness  | Readiness after schema and cross-statement semantic checks.                                           |
| Exhaustive basis    | Owner-local `CON-*` that explicitly closes an enumerated external boundary.                           |
| Semantic audit      | Read-only checks over IWE-supplied owner data for cross-statement, filesystem, and readiness integrity. |
| Accepted intent     | Normative content that a conforming implementation must satisfy.                                      |
| Evidence            | Confirmed or inferred implementation information that does not change accepted intent.                |
| Governing closure   | Task-selected owner plus every owner whose accepted claims govern that task.                           |
| Implementation freedom | Whether contract-equivalent implementations are allowed or accepted architecture also constrains conformance. |
