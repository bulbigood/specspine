# Workflow scheduling

Workflow scheduling turns tenant recurrence rules into stable workflow-trigger occurrences.

## Responsibility

It owns schedule definitions, time zones, next occurrence, pause/resume, missed-run policy, and occurrence identity.

## Boundaries

- Schedule-trigger binding belongs to [workflow triggers](workflow-triggers.md).
- Execution creation belongs to [workflow executions](workflow-executions.md).
- Worker timing belongs to [background jobs](background-jobs.md).

## Behavior

Each due occurrence has a deterministic identity derived from schedule and intended instant. Claiming is distributed and at least once, while execution creation deduplicates that identity. Updating a schedule affects future occurrences only. Time-zone transitions follow the schedule's explicit local-time policy.

## Open questions

- Should missed occurrences be skipped, coalesced, or replayed, and what maximum catch-up window applies?


