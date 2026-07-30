# Scenario: initialize a project

## Initial state

No `<spine-root>/` directory exists.

## User request

```text
Create a SpecSpine for a small service that lets teams upload documents,
process them asynchronously, and search the extracted content.
```

## Expected behavior

The skill should:

- create root `README.md`, `_INDEX.md`, and `specspine.json`;
- create a small set of top-level concept specifications;
- keep initial specifications concise;
- record important unknowns as open questions;
- avoid creating files for individual endpoints, jobs, tables, or classes;
- avoid modifying source code.

## Failure indicators

- a large speculative architecture is created immediately;
- implementation details are presented as accepted decisions;
- the result lacks an architecture entry point;
- the same concept is defined in several files.
