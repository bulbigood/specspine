# Application

**ID:** `application` · **Kind:** `concept`

**Summary:** Provides the user-facing workflows for managing an organization, its members, and its subscription.

## Responsibility

- expose the product's primary workflows;
- coordinate identity and billing capabilities;
- enforce the active organization context.

## Boundaries

Authentication belongs to [Identity](identity.md).

Subscription state and payment-provider communication belong to
[Billing](billing.md).

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Identity](identity.md) | Provides neighboring architectural context |
| `related-to` | [Billing](billing.md) | Provides neighboring architectural context |
| `related-to` | [Operations](operations.md) | Provides neighboring architectural context |

## Constraints

- Billing workflows must preserve
  [DEC-idempotent-provider-events](billing.md).

## Open questions

- Which workflows remain available when a subscription is past due?
