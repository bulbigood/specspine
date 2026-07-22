# Organizations

Organizations are the tenant boundary for business data, membership, and
tenant-scoped API operations.

## Responsibility

This capability owns stable organization identity, display metadata,
lifecycle state, and resolution of the organization context used by
downstream capabilities.

## Boundaries

- Human participation and tenant roles belong to
  [organization membership](organization-membership.md).
- Global user identity and credentials remain with
  [user management](user-management.md) and
  [authentication](authentication.md).
- Permission evaluation belongs to [access control](access-control.md).
- Persistence owns generic storage mechanics, not tenant lifecycle policy.

## Interfaces

- `POST /v1/organizations` creates an organization and establishes the caller
  as its initial owner.
- `GET /v1/organizations` lists organizations visible to the caller.
- `GET /v1/organizations/{organizationId}` returns tenant metadata when the
  caller has membership-based access.
- `PATCH /v1/organizations/{organizationId}` changes mutable tenant metadata.
- `DELETE /v1/organizations/{organizationId}` begins tenant closure rather
  than synchronously erasing related records.

Every organization-scoped API operation carries an unambiguous
`organizationId`; ambient default-tenant selection is not authoritative.

## Lifecycle

An organization moves from active to closing and then closed. Closing blocks
new business activity while allowing authorized export and cleanup work.

<!-- specspine:semantic-ids:begin -->
## Decisions

- **DEC-explicit-tenant-context** — Tenant-scoped operations identify their
  organization explicitly and never infer authority from a user's first or
  most recent membership.

## Constraints

- **CON-tenant-isolation** — Data owned by one organization must not be
  returned, mutated, or referenced through another organization's API context.
<!-- specspine:semantic-ids:end -->

## Open questions

- Must the last owner transfer ownership before leaving or closing an
  organization?
- Which retention policy governs closed organization records?

Retention execution and holds are owned by [data retention](data-retention.md);
the exact commercial and regulatory durations remain unresolved.

## Relationships

- [API runtime](api-runtime.md)
- [Persistence](persistence.md)

