# Application

Provides the user-facing workflows for managing an organization, its members,
and its subscription.

## Responsibility

- expose the product's primary workflows;
- coordinate identity and billing capabilities;
- enforce the active organization context.

## Boundaries

Authentication belongs to [Identity](identity.md).

Subscription state and payment-provider communication belong to
[Billing](billing.md).

## Relationships

### Depends on

- [Identity](identity.md)
- [Billing](billing.md)

### Related

- [Operations](operations.md)

## Constraints

- Billing workflows must preserve
  [DEC-idempotent-provider-events](billing.md).

## Open questions

- Which workflows remain available when a subscription is past due?
