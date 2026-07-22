# Polling triggers

Polling triggers collect provider changes when no trustworthy push mechanism is available.

## Responsibility

They own poll cadence, due-work scheduling, connection health interaction, batch bounds, cursor lease use, and recovery from partial collection.

## Boundaries

- Provider event semantics belong to [connector triggers](connector-triggers.md).
- Progress belongs to [sync cursors](sync-cursors.md).
- Provider capacity belongs to [external rate limits](external-rate-limits.md).
- General timing and retries belong to [background jobs](background-jobs.md).

## Behavior

Each enabled binding schedules bounded collection work. A poll reads from its committed cursor, durably emits normalized events, then advances progress. Authorization failure marks the connection for reauthorization; provider throttling reschedules without advancing the cursor.

## Constraints

- Concurrent polls cannot advance the same cursor under different leases.
- Polling frequency respects tenant entitlement and provider quota constraints.


