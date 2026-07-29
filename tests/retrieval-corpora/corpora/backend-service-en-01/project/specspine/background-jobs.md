# Background jobs

**ID:** `background-jobs` · **Kind:** `concept`

**Summary:** Owns the durable architectural concept `background-jobs`.

## Responsibility

Background jobs provide durable execution, leases, checkpoints, concurrency
limits, and dead-letter storage for carrier, payment, and notification work.

## Execution

A worker claims a lease, loads tenant context, and records the attempt before
calling an external system. Lost leases prevent completion writes. Queue
delivery may repeat, so every handler needs a stable operation identity.

Workers consume classification, attempt budgets, exponential backoff, and
jitter from [Retry policy](retry-policy.md). The queue owns wake-up mechanics
but not the business meaning of a retryable error.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Persistence](persistence.md) | Provides neighboring architectural context |
| `related-to` | [Observability](observability.md) | Provides neighboring architectural context |
| `related-to` | [Carrier integration](carrier-integration.md) | Provides neighboring architectural context |
