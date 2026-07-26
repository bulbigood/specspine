# Scenario: exhaustive Map with unknown producer capacity

The environment supports fresh subagents but does not expose capacity in
advance. One producer start succeeds; additional starts may fail while it is
active.

## User request

```text
Use `$specspine-map` to cover the whole repository.
```

## Expected behavior

The orchestrator must count only confirmed producer handles, assign a task only
after start succeeds, continue useful root inventory/integration work while a
producer runs, and retry ready ToDo with newly created producers as slots
become available.

Every successful producer handles one task and terminates after one checkpoint.
A failed start leaves the task in ToDo. A completed producer is never reused.

## Failure indicators

- a task becomes assigned before a producer handle exists;
- the orchestrator waits for producers that were never created;
- a failed start loses or blocks the ToDo;
- a completed producer receives another task;
- capacity uncertainty is treated as architectural blockage while a retry is
  still possible.
