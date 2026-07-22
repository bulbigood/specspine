# Payment methods

Payment methods manage provider-tokenized instruments used to collect a billing account's invoices.

## Responsibility

They own safe instrument references, display metadata, default selection, verification status, attachment, detachment, and expiry signaling.

## Boundaries

- Sensitive payment data collection occurs through the payment provider and is not owned by RelayHub.
- Collection attempts belong to [payment processing](payment-processing.md).
- Customer identity belongs to [billing accounts](billing-accounts.md).

## Interfaces

Billing administrators initiate provider-hosted setup, confirm the resulting safe reference, list instruments, choose a default, and detach unused methods. Responses expose only brand, trailing digits, expiry, and status supplied for display.

## Constraints

- RelayHub never receives or persists raw card numbers or security codes.
- A method required by an in-flight collection attempt cannot be detached until that attempt reaches a recoverable outcome.


