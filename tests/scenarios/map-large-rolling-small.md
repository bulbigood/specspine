# Scenario: rolling large-Map orchestration with two worker slots

## Existing SpecSpine

The live Spine contains only its runtime composition. Identity, job execution,
and telemetry are the only material unmapped responsibilities in this
controlled repository.

## User request

```text
Use `$specspine-map-large` to complete this repository map. The environment
provides individual worker completion and exactly two safe mapping-worker slots
in addition to the orchestrator. Map the three independent architectural
questions: identity sessions, background job execution, and telemetry export.
Use `.specspine-map-run/` as the disposable run root and the corresponding
private roots `.specspine-map-run/staging/identity/`,
`.specspine-map-run/staging/jobs/`, and
`.specspine-map-run/staging/telemetry/`. Producers can load the required mapper
from `.eval/companions/specspine-map/SKILL.md`. There are no other material
coverage gaps in this fixture. Do not run SpecSpine Doctor.
```

## Expected behavior

The orchestrator should start two independent producers, refill the first freed
slot with the third question before consuming staged files, publish candidates
unchanged, normalize once, and remove the successful disposable run root.

## Failure indicators

- fewer or more than three producer questions are dispatched;
- the first two slots are not filled before waiting;
- a completed candidate is read or moved before the replacement starts;
- producer prompts omit the mapper or mix several architectural questions;
- source or tests change;
- the disposable run root remains after success.
