# Authorization

**ID:** `authorization` · **Kind:** `concept`

Owns the durable architectural concept `authorization`.

## Responsibility

Authorization maps authenticated principals to tenant roles and machine
scopes. Every order, payment, shipment, and callback lookup is constrained by
the resolved tenant before resource-level policy is evaluated.

## Policy

Operators may inspect deliveries but cannot rotate credentials. Administrators
may manage API keys and webhook subscriptions. Service clients receive the
minimum scopes required for order creation or status synchronization.

## Boundaries

This document owns access decisions, not identity proof, request throttling, or
audit retention.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Authentication](authentication.md) | Provides neighboring architectural context |
| `related-to` | [HTTP request pipeline](http-request-pipeline.md) | Provides neighboring architectural context |
