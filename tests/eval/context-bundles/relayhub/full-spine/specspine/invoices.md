# Invoices

Invoices present immutable billed periods, usage, adjustments, taxes, collection status, and resulting balance.

## Responsibility

They own invoice identity and numbering, line-item snapshots, totals, period, finalization, payment association, credit adjustments, and customer-visible document access.

## Boundaries

- Source consumption belongs to [usage metering](usage-metering.md).
- Price and included allowances belong to [plans and entitlements](plans-entitlements.md).
- Collection belongs to [payment processing](payment-processing.md).

## Lifecycle

An invoice is draft, finalized, open, paid, void, or uncollectible. Draft totals may be recomputed; finalization freezes monetary lines and tax evidence. Later corrections create credits or adjustments rather than mutating the finalized record.

## Constraints

- Invoice access is restricted to its billing account and billing-authorized tenant principals.
- Finalized invoices remain reproducible after plan or customer metadata changes.


