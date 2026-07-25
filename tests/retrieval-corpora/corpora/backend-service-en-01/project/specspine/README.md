# ParcelPilot architecture

**ID:** `project-architecture` · **Kind:** `index`

Describes the canonical architecture of this bundled fixture.

## Purpose

ParcelPilot is a multi-tenant backend service that accepts delivery orders,
reserves payment, purchases carrier labels, and reports shipment progress to
merchant systems. HTTP APIs handle the control plane while workers perform
recoverable carrier and notification operations.

## Architecture map

### Request and identity

- [HTTP request pipeline](http-request-pipeline.md) — authenticates, validates,
  and normalizes API requests.
- [Authentication](authentication.md) — proves merchant and service identities.
- [Authorization](authorization.md) — evaluates tenant roles and scopes.
- [Rate limits](rate-limits.md) — protects API and tenant capacity.

### Delivery lifecycle

- [Order lifecycle](order-lifecycle.md) — owns delivery-order states and cancellation.
- [Payment processing](payment-processing.md) — owns authorization, capture, and refunds.
- [Carrier integration](carrier-integration.md) — purchases labels and polls carriers.
- [Retry policy](retry-policy.md) — owns retry classification and scheduling.
- [Background jobs](background-jobs.md) — executes durable asynchronous work.
- [Webhook delivery](webhook-delivery.md) — signs and delivers merchant callbacks.

### Platform operations

- [Persistence](persistence.md) — owns transactions and durable storage.
- [Configuration](configuration.md) — defines runtime configuration boundaries.
- [Observability](observability.md) — defines logs, metrics, and traces.
- [Incident response](incident-response.md) — coordinates service restoration.

## System shape

The API stores accepted intent before enqueueing external work. Workers use the
same tenant-scoped database but do not reuse request transactions. Carrier,
payment, and webhook calls share operational libraries while their owning
documents define separate business semantics.

## Coverage

### Mapped

- [HTTP request pipeline](http-request-pipeline.md) — bundled fixture is mapped.
- [Authentication](authentication.md) — bundled fixture is mapped.
- [Authorization](authorization.md) — bundled fixture is mapped.
- [Rate limits](rate-limits.md) — bundled fixture is mapped.
- [Order lifecycle](order-lifecycle.md) — bundled fixture is mapped.
- [Payment processing](payment-processing.md) — bundled fixture is mapped.
- [Carrier integration](carrier-integration.md) — bundled fixture is mapped.
- [Retry policy](retry-policy.md) — bundled fixture is mapped.
- [Background jobs](background-jobs.md) — bundled fixture is mapped.
- [Webhook delivery](webhook-delivery.md) — bundled fixture is mapped.
- [Persistence](persistence.md) — bundled fixture is mapped.
- [Configuration](configuration.md) — bundled fixture is mapped.
- [Observability](observability.md) — bundled fixture is mapped.
- [Incident response](incident-response.md) — bundled fixture is mapped.

### Partially mapped

- No partially mapped bundled areas.

### Unmapped

- No known unmapped bundled areas.
