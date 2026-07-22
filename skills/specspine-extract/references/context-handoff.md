# Architecture context handoff

A context handoff is a temporary, task-oriented projection of the long-lived
SpecSpine. It transfers the smallest useful architectural context to a feature
workflow or coding agent. It is not a feature specification, implementation
plan, or claim of code conformance.

Use this shape and omit empty sections:

```markdown
# Architecture context handoff

## Change intent

## Primary specification

## Required specifications

## Potentially affected specifications

## Architectural decisions and constraints

## Decision sources

## Relevant observations

## Unconfirmed inferences

## Blocking questions

## Expected architectural outcome
```

Name one canonical primary owner when one exists. Separate specifications that
must be read from those that may require an architectural update; omit merely
related context unless it is needed for navigation.
`Required` means required to understand the change safely, not necessarily a
file expected to change. Use `Potentially affected` only when the specification
is not needed to establish the handoff but may need later review or revision.

Write specification addresses as repository-root-relative paths including the
resolved spine root. Do not use absolute paths, leading `/`, or paths relative
to the handoff location.

When a relevant source statement already has a semantic ID, name its ID and
repository-root-relative owner path. Do not invent IDs in a handoff.

```markdown
- Preserve `CON-retry-limit` from `specspine/job-processing.md`.
```

Treat external decision sources as provenance, not new authority. Carry
evidence baselines when observation freshness matters. Preserve unconfirmed
inferences and blocking questions without resolving them.
