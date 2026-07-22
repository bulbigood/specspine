# Connector triggers

Connector triggers define versioned external signals that may begin workflow executions.

## Responsibility

They own trigger identity, delivery strategy, configuration schema, emitted event schema, deduplication identity, and cursor semantics.

## Boundaries

- HTTPS reception belongs to [inbound webhooks](inbound-webhooks.md).
- Scheduled collection belongs to [polling triggers](polling-triggers.md).
- Starting workflow runs belongs to [workflow triggers](workflow-triggers.md).
- Cursor persistence belongs to [sync cursors](sync-cursors.md).

## Behavior

A trigger normalizes provider input into a versioned event carrying tenant, connection, provider event identity, occurrence time, and payload. Duplicate provider delivery does not create duplicate workflow starts under the same trigger binding.

## Constraints

- Trigger events never contain connection secrets.
- Every event records the connector and trigger versions used for normalization.


