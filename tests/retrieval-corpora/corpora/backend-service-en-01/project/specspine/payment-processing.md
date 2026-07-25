# Payment processing

**ID:** `payment-processing` · **Kind:** `concept`

Owns the durable architectural concept `payment-processing`.

## Responsibility

Payment processing owns authorization before label purchase, capture after
carrier acceptance, refunds, and reconciliation of provider outcomes.

## Refund idempotency

Each refund uses the tuple of tenant, payment, refund reason, and command key
as its stable operation identity. Repeating the same command returns the
recorded refund; changing the amount under a reused key is a conflict. The
provider request and local result are recovered through a durable payment
operation rather than a long database transaction.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-refund-idempotent** — A repeated refund command must never create a
  second provider refund for the same operation identity.
<!-- specspine:semantic-ids:end -->

## Boundaries

Order cancellation decides whether release is needed. This capability owns the
financial command and its replay semantics.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Order lifecycle](order-lifecycle.md) | Provides neighboring architectural context |
| `related-to` | [Retry policy](retry-policy.md) | Provides neighboring architectural context |
| `related-to` | [Persistence](persistence.md) | Provides neighboring architectural context |
