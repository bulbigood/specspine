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
other material coverage gaps in this fixture. Spawn every producer with
`fork_turns=none`. Do not override its model, reasoning effort, or agent type:
use the harness-pinned subagent defaults. Keep model routing outside the
producer command. Do not run SpecSpine Doctor.
```

## Expected behavior

The orchestrator should start two independent producers, refill the first freed
slot with the third zone before consuming staged files, publish candidates
unchanged, normalize once, and remove the successful disposable run root.

## Failure indicators

- fewer than three zone assignments or more than one retry are dispatched;
- the first two slots are not filled before waiting;
- one producer receives more than one architectural zone;
- producer prompts omit the inline mapping contract or tell workers to load it;
- source or tests change;
- the disposable run root remains after success.
