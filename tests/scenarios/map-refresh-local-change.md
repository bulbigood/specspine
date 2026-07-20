# Scenario: refresh after a local architectural change

## Existing SpecSpine

```text
<spine-root>/
├── README.md
├── api-server.md
├── background-processing.md
├── persistence.md
└── operations.md
```

## Repository change

A separate email-delivery worker and queue were added.

## User request

```text
Update the SpecSpine for the email worker.
```

## Expected behavior

The skill should:

- inspect the new worker, queue integration, configuration, and representative
  tests;
- update only the affected specification area;
- decide whether notification delivery deserves its own specification;
- update top-level navigation only when useful;
- preserve unrelated specifications;
- report observed facts and unresolved ownership questions.

## Failure indicators

- the whole repository is remapped;
- unrelated specifications are rewritten;
- the worker's implementation internals are exhaustively documented;
- code is modified.
