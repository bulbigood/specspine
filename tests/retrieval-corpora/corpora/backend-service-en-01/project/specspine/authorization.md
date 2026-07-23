# Authorization

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

- [Authentication](authentication.md)
- [HTTP request pipeline](http-request-pipeline.md)
