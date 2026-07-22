# Workflow triggers

Workflow triggers bind one published workflow revision to the conditions that may create executions.

## Responsibility

They own manual, connector-event, schedule, and API invocation bindings, input schema, enablement, and start deduplication policy.

## Boundaries

- External signal normalization belongs to [connector triggers](connector-triggers.md).
- Recurrence calculation belongs to [workflow scheduling](workflow-scheduling.md).
- Created run state belongs to [workflow executions](workflow-executions.md).

## Interfaces

Authorized callers may manually run an active workflow with validated input. Connector events and schedule occurrences carry stable source identities. Trigger acceptance records the workflow revision and environment before execution is enqueued.

## Constraints

- Repeated delivery of the same trigger identity cannot create multiple executions for one binding.
- Paused or archived workflows reject new starts without altering existing runs.


