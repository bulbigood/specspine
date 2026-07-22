# Billing accounts

Billing accounts identify the commercial customer responsible for an organization's RelayHub service.

## Responsibility

They own billing identity, legal and tax metadata, billing contacts, currency, provider-customer reference, and delinquency state.

## Boundaries

- Tenant product ownership belongs to [organizations](organizations.md).
- Commercial access belongs to [plans and entitlements](plans-entitlements.md).
- Charges and collection belong to [subscriptions](subscriptions.md), [payment methods](payment-methods.md), and [invoices](invoices.md).

## Behavior

An organization has one active billing account, while an enterprise billing account may fund several organizations when explicitly associated. Billing administrators can update safe metadata but cannot directly alter provider-owned balances or settled invoices.

## Constraints

- Provider customer identifiers never authorize tenant access.
- Tax and billing metadata are restricted to billing-authorized principals and excluded from general organization responses.


