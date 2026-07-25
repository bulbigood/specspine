# Order lifecycle

**ID:** `order-lifecycle` · **Kind:** `concept`

Owns the durable architectural concept `order-lifecycle`.

## Responsibility

This capability owns the delivery order state machine: draft, accepted,
labeling, ready, in-transit, delivered, canceled, and failed.

## Cancellation

A draft or accepted order can be canceled immediately. Once label purchase
starts, cancellation records intent in the same database transaction as the
state version and schedules carrier cleanup after commit. An in-transit order
cannot be canceled through the API.

Concurrent commands use optimistic state versions. A duplicate cancellation
with the same idempotency key replays the original result. Payment release is a
separate follow-up owned by [Payment processing](payment-processing.md).

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-cancellation-after-commit** — Carrier cleanup and payment release may
  start only after cancellation intent commits successfully.
<!-- specspine:semantic-ids:end -->

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Persistence](persistence.md) | Provides neighboring architectural context |
| `related-to` | [Carrier integration](carrier-integration.md) | Provides neighboring architectural context |
| `related-to` | [Payment processing](payment-processing.md) | Provides neighboring architectural context |
