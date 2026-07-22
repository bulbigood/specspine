# Audit log

The audit log preserves tenant-scoped, attributable evidence of security and
administrative actions without becoming workflow state.

## Responsibility

It owns immutable audit-event identity, actor attribution, tenant context,
action, target reference, outcome, occurrence time, request correlation, safe
metadata, retention, and authorized query.

## Boundaries

- Domain capabilities decide that an action occurred and remain owners of its
  business state.
- [Access control](access-control.md) supplies human or service-account actor
  identity.
- [Event delivery](event-delivery.md) may transport audit facts but cannot be
  the only durable audit record.
- Operational logs belong to
  [configuration and operations](configuration-operations.md) and are not a
  substitute for audit history.

## Interfaces

- `GET /v1/organizations/{organizationId}/audit-events` queries events by time,
  actor, action, target type, target id, and outcome.
- `GET /v1/organizations/{organizationId}/audit-events/{auditEventId}` returns
  one immutable event with safe metadata.

Internal capability interfaces append audit events within the action's
recoverable boundary. Credentials, tokens, webhook secrets, and password
material are prohibited from audit metadata.

## Behavior

Audit query is tenant-scoped and ordered by occurrence time plus stable event
identity. Records are append-only; correction creates a linked compensating
record rather than replacing history.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-audit-immutable** — Accepted audit events cannot be updated or deleted
  through application APIs.
- **CON-audit-attribution** — Sensitive mutations identify the human or machine
  principal, tenant context, and request correlation that caused them.
<!-- specspine:semantic-ids:end -->

## Open questions

- Which actions are mandatory audit coverage beyond credential, membership,
  service-account, webhook, and organization lifecycle changes?
- What retention and export guarantees apply to closing organizations?

## Relationships

- [Organization membership](organization-membership.md)
- [Service accounts](service-accounts.md)
- [Persistence](persistence.md)

