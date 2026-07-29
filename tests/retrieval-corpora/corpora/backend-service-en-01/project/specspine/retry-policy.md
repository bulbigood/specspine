# Retry policy

**ID:** `retry-policy` · **Kind:** `concept`

**Summary:** Owns the durable architectural concept `retry-policy`.

## Responsibility

This policy owns retry classification and scheduling for external operations.

## Rules

Transient failures use exponential backoff with full jitter. The delay is
capped, and every operation has an attempt budget. Permanent failures are
never retried. Provider hints may extend the next delay but cannot exceed the
operation deadline.

<!-- specspine:semantic-ids:begin -->
## Decisions

- **DEC-full-jitter-retries** — External retries use full jitter to avoid
  synchronized recovery traffic.
<!-- specspine:semantic-ids:end -->

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Carrier integration](carrier-integration.md) | Provides neighboring architectural context |
| `related-to` | [Background jobs](background-jobs.md) | Provides neighboring architectural context |
