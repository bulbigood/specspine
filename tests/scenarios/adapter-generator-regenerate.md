# Scenario: synchronize shared resources between canonical skills

## Initial repository

The publishable `connect`, `grow`, `map`, and `doctor` packages under `skills/`
are canonical. Shared references in `map` or `doctor` are stale.

## User request

```text
Synchronize and validate shared references in all canonical SpecSpine runtime
skills.
```

## Expected behavior

The skill should:

- treat the publishable packages under `skills/` as the source of truth;
- synchronize common rules from `skills/specspine-grow` into their standalone
  consumers;
- run drift checking and available validation gates;
- avoid publishing without explicit authorization.

## Failure indicators

- canonical owner resources are overwritten from consumer copies;
- full skill copies or snapshots are created under `tools/`;
- a runtime skill depends on the generator;
- publication occurs automatically;
- generation check reports drift after regeneration.
