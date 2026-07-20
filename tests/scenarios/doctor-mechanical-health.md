# Scenario: diagnose mechanical SpecSpine defects

## Existing SpecSpine

The architecture index links to `application.md`. The graph also contains an
unreachable specification, a broken link, an invalid semantic-ID reference,
and an empty optional section.

## User request

```text
Check this SpecSpine for mechanical problems.
```

## Expected behavior

The skill should:

- load current bundled format and semantic rules;
- run the deterministic checker;
- report broken links, reachability, semantic-ID, and empty-section findings
  separately;
- include affected paths and evidence;
- remain read-only;
- avoid claiming formal validity or completeness.

## Failure indicators

- specifications are modified;
- bundled rules are ignored or reconstructed from memory;
- warnings are presented as proof of invalid architecture;
- semantic findings are invented without reading the relevant documents.
