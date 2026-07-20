# Minimal SaaS architecture

## Purpose

A small multi-tenant SaaS application where organizations manage members and
paid subscriptions.

## Architecture map

- [Application](application.md) — coordinates the product's main user-facing behavior.
- [Identity](identity.md) — authenticates users and associates them with organizations.
- [Billing](billing.md) — owns subscription state and payment-provider integration.
- [Operations](operations.md) — covers deployment, configuration, and service health.

## System-wide decisions

- Organizations are the tenant boundary.
- Authentication method and application session are separate concerns.
- External payment-provider events may be delivered more than once.

## Open questions

- Can a user belong to more than one organization?
- Is a free plan represented as a subscription?
