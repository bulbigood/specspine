# Persistence

## Responsibility

Persistence owns tenant-scoped relational storage, transaction boundaries,
optimistic versions, migrations, and connection health.

## Transactions

Capability handlers commit state and an outbox record in one database
transaction. External payment, carrier, and webhook calls never run while a
transaction is open. Workers claim outbox records after commit and use
operation identities for replay.

Order cancellation writes its state transition atomically, but the order
capability decides which transitions are legal. Payment processing owns refund
idempotency rather than the database layer.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-no-network-in-transaction** — Network operations must not execute
  inside a database transaction.
<!-- specspine:semantic-ids:end -->

## Relationships

- [Order lifecycle](order-lifecycle.md)
- [Background jobs](background-jobs.md)
