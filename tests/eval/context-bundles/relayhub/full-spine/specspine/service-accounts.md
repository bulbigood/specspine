# Service accounts

Service accounts represent non-human principals that call organization-scoped
APIs without borrowing a user's identity or session.

## Responsibility

This capability owns service-account identity, display metadata, lifecycle,
tenant ownership, and the permission scopes granted to each machine principal.

## Boundaries

- Secret issuance and verification belong to
  [API credentials](api-credentials.md).
- Human tenant participation belongs to
  [organization membership](organization-membership.md).
- [Access control](access-control.md) evaluates the resulting principal and
  scopes but does not own service-account lifecycle.
- The owning tenant is defined by [organizations](organizations.md).

## Interfaces

- `POST /v1/organizations/{organizationId}/service-accounts` creates a machine
  principal with an explicit scope set.
- `GET /v1/organizations/{organizationId}/service-accounts` lists principals
  without returning credential material.
- `GET /v1/organizations/{organizationId}/service-accounts/{serviceAccountId}`
  returns identity, state, and granted scopes.
- `PATCH /v1/organizations/{organizationId}/service-accounts/{serviceAccountId}`
  changes metadata or scopes.
- `DELETE /v1/organizations/{organizationId}/service-accounts/{serviceAccountId}`
  disables the principal and revokes its credentials.

## Lifecycle

A service account is active or disabled. Disabling it immediately prevents all
of its credentials from authenticating, independently of their stored expiry.

## Decisions

- Service accounts never share identifiers or role records with human users.
- Scopes are allow-listed capabilities; absence of a scope denies access.

## Constraints

- A service account belongs to exactly one organization.
- A machine principal cannot perform global user or platform administration.

## Open questions

- Is a fixed scope vocabulary sufficient, or must organizations define custom
  scopes?
- Should disabled service-account identities remain visible indefinitely for
  audit attribution?

## Relationships

- [Audit log](audit-log.md)
- [Persistence](persistence.md)

