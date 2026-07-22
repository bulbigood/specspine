# Subscriptions

Subscriptions bind a billing account to a versioned RelayHub plan over renewable service periods.

## Responsibility

They own subscription identity, plan version, period boundaries, trial, cancellation intent, provider reference, and commercial status.

## Boundaries

- Feature meaning belongs to [plans and entitlements](plans-entitlements.md).
- Payment collection belongs to [payment processing](payment-processing.md).
- Period charges belong to [invoices](invoices.md).

## Lifecycle

A subscription is trialing, active, past-due, cancellation-scheduled, cancelled, or suspended. Plan changes become effective according to an explicit immediate or next-period policy. Provider notifications update state idempotently and out-of-order events cannot regress a newer confirmed status.

## Constraints

- The payment provider is authoritative for collection outcome, while RelayHub remains authoritative for product entitlement activation.
- Cancellation preserves billing and usage history.


