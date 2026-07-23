# Background jobs

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

- [Persistence](persistence.md)
- [Observability](observability.md)
- [Carrier integration](carrier-integration.md)
