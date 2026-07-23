# HTTP request pipeline

## Responsibility

The pipeline assigns a request ID, authenticates the caller, resolves the
tenant, validates input, applies API rate limits, and translates failures into
the public error envelope.

## Boundaries

It transports idempotency keys but does not define payment or order replay
semantics. It may retry neither handlers nor external provider calls. Durable
recovery belongs to [Background jobs](background-jobs.md), while retry
classification belongs to [Retry policy](retry-policy.md).

## Processing order

Authentication precedes tenant authorization. Schema validation precedes the
transaction opened by the capability handler. Logs include request and tenant
identifiers but redact credentials and webhook secrets.

## Relationships

- [Authentication](authentication.md)
- [Authorization](authorization.md)
- [Rate limits](rate-limits.md)
