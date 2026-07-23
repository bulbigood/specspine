# Scenario: direct Map comparison on three independent areas

## Existing SpecSpine

The live Spine contains only runtime composition. Identity sessions, background
job execution, and telemetry export are the only material unmapped
responsibilities.

## User request

```text
Use `$specspine-map` to complete the map of this repository in one bounded
mapping operation. Map the three independent architectural areas: identity
sessions, background job execution, and telemetry export. There are no other
material coverage gaps in this fixture. Update only `specspine/`; do not run
SpecSpine Doctor.
```

## Expected behavior

Map should inspect the three small evidence slices, create the smallest useful
set of specifications, update navigation, and leave source and tests unchanged.

## Failure indicators

- any of the three responsibilities is omitted;
- source or tests change;
- the resulting Spine has broken links or invalid semantic IDs;
- implementation detail dominates the specifications.
