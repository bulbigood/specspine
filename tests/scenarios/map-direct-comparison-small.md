# Scenario: direct Map comparison on six independent areas

## Existing SpecSpine

The live Spine contains only runtime composition. Identity sessions, background
job execution, telemetry export, notification delivery, search indexing, and
webhook ingestion are the only material unmapped responsibilities.

## User request

```text
Use `$specspine-map` to deepen the architecture map of this whole repository by
one useful mapping step.
```

## Expected behavior

Map should inspect the repository shape, apply one smallest coherent
specification change, report further depth, and leave source and tests
unchanged.

## Failure indicators

- source, tests, or configuration change;
- the resulting Spine has broken links or invalid semantic IDs;
- implementation detail dominates the specifications.
