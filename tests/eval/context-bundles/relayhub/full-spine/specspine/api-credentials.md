# API credentials

API credentials prove a service account's identity while allowing secrets to
rotate and revoke independently of the principal.

## Responsibility

This capability owns credential issuance, one-time secret disclosure, stored
secret verification material, expiry, rotation overlap, revocation, and safe
credential identification in operational records.

## Boundaries

- Principal identity and permissions belong to
  [service accounts](service-accounts.md).
- Request authentication and authorization belong to
  [access control](access-control.md).
- Human access and refresh tokens remain with
  [token lifecycle](token-lifecycle.md).

## Interfaces

- `POST /v1/organizations/{organizationId}/service-accounts/{serviceAccountId}/credentials`
  issues a credential and returns its secret exactly once.
- `GET /v1/organizations/{organizationId}/service-accounts/{serviceAccountId}/credentials`
  lists safe identifiers, creation time, expiry, and status.
- `DELETE /v1/organizations/{organizationId}/service-accounts/{serviceAccountId}/credentials/{credentialId}`
  revokes one credential.

Machine requests present a credential identifier and secret. Authentication
returns the service-account principal, owning organization, and effective
scopes; it never returns stored verification material.

## Lifecycle

Credentials are active, expired, or revoked. Rotation creates a new credential
before the old one is revoked so clients can migrate without changing the
service-account identity.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-api-secret-one-time** — Raw API credential secrets are returned only
  at creation and are never recoverable afterward.
- **CON-api-secret-storage** — Persistent storage contains only
  non-reversible credential verification material.
<!-- specspine:semantic-ids:end -->

## Open questions

- What maximum credential lifetime and rotation-overlap period are required?
- Must authentication failures expose rate-limit information to machine
  clients?

## Relationships

- [Request pipeline](request-pipeline.md)
- [Persistence](persistence.md)

