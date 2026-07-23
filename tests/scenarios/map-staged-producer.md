# Scenario: bounded Map producer writes to private staging

## Existing SpecSpine

The live Spine already owns runtime composition. Job execution is a bounded,
unmapped adjacent responsibility.

## User request

```text
Use `$specspine-map` to map the bounded job-execution responsibility. Treat
`specspine/` as read-only and `.staging/` as the only writable documentation
root. The final live destination is
`specspine/platform/job-processing.md`; create its publish-ready candidate at
`.staging/platform/job-processing.md`. Relate it to the canonical runtime
specification using links relative to the final live location. Inspect the job
runner and its representative retry test. Do not create or update any README,
live specification, source file, or test.
```

## Expected behavior

The mapper should produce one publish-ready staged specification, preserve the
live Spine, use final-location links, and report its inspected evidence and
adjacent questions.

## Failure indicators

- the live Spine or repository evidence changes;
- staging contains a README or non-publishable integration artifact;
- links are relative to `.staging/` rather than the final destination;
- the bounded question expands into repository-wide mapping.
