# Carrier integration

## Responsibility

Carrier integration maps internal parcels to provider label requests, stores
carrier references, polls shipment status, and normalizes provider events.

## Provider calls

The adapter sends idempotency keys when supported. Timeouts and throttling are
classified as transient; invalid addresses and rejected service levels are
permanent. Recoverable calls are scheduled as background jobs.

The carrier client observes the shared retry policy: exponential backoff,
bounded attempts, and randomized jitter reduce synchronized retries. It records
attempt outcomes and provider request IDs for operators. The adapter consumes
these rules but does not own retry delays, attempt budgets, or jitter values.

## Label purchase

Label purchase may involve quotation, booking, document download, and status
polling. A worker resumes from the last durable checkpoint after a crash.
Duplicate booking is prevented with an operation key even when the provider
does not support native idempotency.

## Failure handling

When attempts are exhausted, the job is quarantined for inspection. Operators
can replay it only after confirming whether the carrier accepted the previous
request. Incident procedures may pause one provider without stopping other
carriers.

## Relationships

- [Retry policy](retry-policy.md)
- [Background jobs](background-jobs.md)
- [Order lifecycle](order-lifecycle.md)
- [Observability](observability.md)
