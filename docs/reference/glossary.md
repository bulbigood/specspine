# Specspine v5 glossary

| Term                | Meaning                                                                                               |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| Owner               | One canonical specification represented by an IWE document.                                           |
| Document key        | Current canonical owner address assigned by IWE; migrated by `iwe rename`.                            |
| Inclusion           | Link-only paragraph; structural parent/child edge.                                                    |
| Reference           | Link inside prose; non-structural graph edge.                                                         |
| Facet               | Declared completeness of architecture, behavior, interfaces, data, failure, quality, or verification. |
| Blocker             | Owner-local `OQ-*` listed in `blockers` and preventing readiness.                                     |
| Normative statement | Accepted constraint on conforming implementations.                                                    |
| Normative asset     | Registered asset with `normative: true`; part of accepted intent.                                     |
| Observation         | Confirmed evidence that is not accepted intent.                                                       |
| Semantic readiness  | Readiness after schema and cross-statement semantic checks.                                           |
| Exhaustive basis    | Owner-local `CON-*` that explicitly closes an enumerated external boundary.                           |
| Semantic audit      | Read-only native-IWE checks for cross-statement, filesystem, and readiness integrity.                 |
