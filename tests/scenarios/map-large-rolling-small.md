# Scenario: rolling large-Map orchestration with two worker slots

## Existing SpecSpine

The live Spine contains only its runtime composition. Identity, job execution,
and telemetry are the only material unmapped architectural zones.

## User request

```text
Use `$specspine-map-large` to complete this repository map. The environment
provides individual completion and exactly two safe mapping-worker slots in
addition to the orchestrator. Map identity sessions, background job execution,
and telemetry export as three separate zones. Use `.specspine-map-run/` as the
disposable run root and private roots `.specspine-map-run/staging/identity/`,
`.specspine-map-run/staging/jobs/`, and
`.specspine-map-run/staging/telemetry/`. Give producers complete self-contained
text commands; they must not load skills or mapping references. There are no
other material coverage gaps in this fixture. The harness configures producer
models outside their commands. Use `.eval/tools/check_spine.py` for candidate
preflight. Do not run SpecSpine Doctor.
```

## Expected behavior

The orchestrator should process the three independent zones concurrently within
the available capacity, publish candidates as they complete without a batch
barrier, normalize once, and remove the successful disposable run root.

## Failure indicators

- fewer than three zone assignments or more than one retry are dispatched;
- one producer receives more than one architectural zone;
- producer prompts omit the inline mapping contract or tell workers to load it;
- source or tests change;
- the disposable run root remains after success.
