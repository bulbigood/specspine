# Sync cursors

Sync cursors preserve progress through provider collections for polling triggers and resumable synchronization.

## Responsibility

They own cursor identity, tenant and connection scope, connector version, committed position, lease, checkpoint, and invalidation.

## Boundaries

- Poll scheduling belongs to [polling triggers](polling-triggers.md).
- Provider pagination semantics belong to [connector triggers](connector-triggers.md).
- Durable storage mechanics belong to [persistence](persistence.md).

## Behavior

A worker leases a cursor, reads from its committed position, emits normalized events, and advances only after those events are durably accepted. Lease expiry permits another worker to resume from the last committed checkpoint. Provider-invalidated cursors enter recovery rather than silently restarting.

## Constraints

- Cursor advancement and durable acceptance of the corresponding event batch form one recoverable boundary.
- Cursor state cannot be reused by another tenant, connection, trigger, or incompatible connector version.


