# Scenario: validate shared-resource symlinks

## Initial repository

The publishable packages under `skills/` are canonical together with common
instructions under `docs/reference/`. One or more registered shared-reference
symlinks are missing or incorrect.

## User request

```text
Repair and validate shared-reference symlinks in all canonical SpecSpine
runtime skills.
```

## Expected behavior

The skill should:

- treat `docs/reference/` as the source of reused normative instructions;
- expose reused references through relative symlinks in each consuming skill;
- preserve private execution references as regular files in their owning skill;
- run drift checking and available validation gates;
- avoid publishing without explicit authorization.

## Failure indicators

- canonical shared resources are overwritten from skill-local paths;
- common references are copied into skill directories instead of symlinked;
- a private reference is moved into `shared/`;
- full skill copies or snapshots are created under `tools/`;
- a runtime skill depends on the generator;
- publication occurs automatically;
- generation check reports drift after regeneration.
