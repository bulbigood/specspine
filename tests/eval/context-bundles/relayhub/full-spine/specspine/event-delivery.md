# Event delivery

Event delivery publishes immutable notifications about accepted state changes
to internal consumers and external-delivery adapters.

## Responsibility

It owns event identity, type, producer, tenant context, occurrence time,
payload version, durable publication, subscriber routing, delivery attempts,
and consumer checkpoints.

## Boundaries

- Producers remain canonical owners of the state described by an event.
- [Background jobs](background-jobs.md) supplies asynchronous execution but
  does not define event meaning.
- [Webhook subscriptions](webhook-subscriptions.md) translates selected events
  into tenant-configured external delivery.
- [Idempotency](idempotency.md) protects subscriber effects during redelivery.

## Interfaces

Producers publish an event only after the associated state transition is
durable. Consumers subscribe by stable event type and receive a versioned
envelope containing event id, organization id, type, occurrence time, and
payload.

## Delivery behavior

Delivery is at least once and may be out of order across independent event
streams. A consumer acknowledges an event only after its owned effect is
durable. Unsupported payload versions fail visibly rather than being silently
discarded.

## Decisions

- Event identifiers remain stable across retries and delivery channels.
- Event payloads describe accepted facts and do not carry commands for
  arbitrary execution.

## Constraints

- Publication and the producer's state transition must not leave a committed
  state change permanently without its corresponding event.
- Consumers cannot mutate or reinterpret the producer's canonical history.

## Open questions

- Is per-aggregate ordering required for any event family?
- How long are event payloads retained after all consumers acknowledge them?

## Relationships

- [Organizations](organizations.md)
- [Persistence](persistence.md)

