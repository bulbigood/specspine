# External benchmark scenario: extract architecture context from a large Grafana Spine

## Fixture

The benchmark controller creates an immutable temporary fixture from
`AGENTS.md` and the complete `specspine/` tree of a caller-selected Grafana
checkout. The fixture is intentionally external to the regular hermetic eval
inventory and is never selected by an eval category.

## User request

Подготовь архитектурный контекст для изменения lifecycle миграции одного
Grafana resource с legacy SQL на Unified Storage. Нужно изменить переключение
legacy → dual-write → unified, обработку недоступного migration log и
served-version guard, не смешав это с выполнением backfill migration или общим
Resource API direction.

## Expected behavior

Extract should identify the dual-write lifecycle as the canonical owner and
include the Unified Storage migration/status contract and Resource API builder
guard as required context. The broader persistence platform and accepted
Resource API migration direction may be included as supporting context.

The handoff must preserve the open question about the runtime authority that
changes migration status. It must not confuse repository provisioning's
interactive dual read/write path with the Unified Storage dual writer.

## Failure indicators

- the canonical dual-write lifecycle owner is omitted;
- Unified Storage migration status or the Resource API served-version guard is
  omitted;
- repository provisioning reconciliation is presented as relevant;
- the agent mutates the fixture;
- Extract is not invoked exactly once in the accelerated arm.
