# Scenario: direct Map comparison on six independent areas

## Existing SpecSpine

The live Spine contains only runtime composition. Identity sessions, background
job execution, telemetry export, notification delivery, search indexing, and
webhook ingestion are the only material unmapped responsibilities.

## User request

```text
Use `$specspine-map` to complete the map of this repository in one bounded
mapping operation. Map the six independent architectural areas: identity
sessions, background job execution, telemetry export, notification delivery,
search indexing, and webhook ingestion. There are no other material coverage
gaps in this fixture. Cite the source, test, and configuration evidence for
each area. Publish them as `identity-sessions.md`,
`background-job-execution.md`, `telemetry-export.md`,
`notification-delivery.md`, `search-indexing.md`, and
`webhook-ingestion.md`. Update only `specspine/`; do not run SpecSpine Doctor.
```

## Expected behavior

Map should inspect the six small evidence slices, create the smallest useful
set of specifications, update navigation, and leave source and tests unchanged.

## Failure indicators

- any of the six responsibilities is omitted;
- source, tests, or configuration change;
- the resulting Spine has broken links or invalid semantic IDs;
- implementation detail dominates the specifications.
