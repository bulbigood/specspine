# Scenario: regenerate autonomous runtime skills

## Initial repository

The maintainer-only `specspine-adapter-generator` contains canonical sources for
`init`, `grow`, `map`, and `doctor`. Generated runtime packages are absent.

## User request

```text
Regenerate and validate all publishable SpecSpine runtime skills.
```

## Expected behavior

The skill should:

- run deterministic generation for all four runtime packages;
- generate self-contained packages without runtime skill dependencies;
- inject common rules from their single canonical authoring source;
- write portable generated manifests;
- run drift checking and available validation gates;
- avoid publishing without explicit authorization.

## Failure indicators

- generated output is hand-written instead of using the script;
- common authoring rules are copied into several source packages;
- a generated runtime skill depends on the generator;
- publication occurs automatically;
- generation check reports drift after regeneration.
