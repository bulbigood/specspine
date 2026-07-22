# Payment processing

Payment processing coordinates external provider collection and refund outcomes with RelayHub billing state.

## Responsibility

It owns payment-attempt identity, provider request idempotency, status reconciliation, failure classification, retries, refunds, and dispute notification.

## Boundaries

- Instruments belong to [payment methods](payment-methods.md).
- Amounts due and settlement presentation belong to [invoices](invoices.md).
- Subscription consequences belong to [subscriptions](subscriptions.md).
- Provider callback reception uses [inbound webhooks](inbound-webhooks.md).

## Behavior

Collection creates one durable attempt before calling the provider. Provider callbacks and active reconciliation converge on the newest authoritative state. Retryable failures schedule bounded collection retries; definitive failure updates invoice and subscription policy. Refunds reference settled charges and preserve the original ledger evidence.

## Constraints

- Every provider mutation carries a stable idempotency identity.
- Callback order cannot regress a terminal settlement or duplicate financial effects.


