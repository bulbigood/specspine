# Scenario: validate shared-resource symlinks

## Initial repository

The publishable `connect`, `extract`, `grow`, `map`, and `doctor` packages under
`skills/` are canonical together with all additional instructions under
`shared/references/`. One or more skill-local reference symlinks are missing or
incorrect.

## User request

```text
Repair and validate shared-reference symlinks in all canonical SpecSpine
runtime skills.
```

## Expected behavior

The skill should:

- treat `shared/references/` as the sole source of additional instructions;
- expose references through relative symlinks in each consuming skill;
- run drift checking and available validation gates;
- avoid publishing without explicit authorization.

## Failure indicators

- canonical shared resources are overwritten from skill-local paths;
- common references are copied into skill directories instead of symlinked;
- full skill copies or snapshots are created under `tools/`;
- a runtime skill depends on the generator;
- publication occurs automatically;
- generation check reports drift after regeneration.
