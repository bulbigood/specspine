# Organization membership

Organization membership binds a global user identity to a tenant and owns the
role used for tenant-scoped authorization.

## Responsibility

It owns invitations, active memberships, tenant roles, role changes, removal,
and the rule that an authenticated identity gains no tenant authority without
an active membership.

## Boundaries

- Organization lifecycle belongs to [organizations](organizations.md).
- Global account state belongs to [user management](user-management.md).
- Authentication proves identity; [access control](access-control.md)
  evaluates membership and requested permissions.
- Notification transport belongs to [email delivery](email-delivery.md).

## Interfaces

- `POST /v1/organizations/{organizationId}/invitations` creates a time-limited
  invitation for an email address and tenant role.
- `POST /v1/organization-invitations/{token}/accept` binds the authenticated
  user to the invitation's organization.
- `GET /v1/organizations/{organizationId}/members` lists active memberships.
- `PATCH /v1/organizations/{organizationId}/members/{userId}` changes a
  member's tenant role.
- `DELETE /v1/organizations/{organizationId}/members/{userId}` removes tenant
  authority without deleting the global user.

## Lifecycle

Invitations are pending, accepted, expired, or revoked. Memberships are active
or removed; accepting the same invitation repeatedly must not create duplicate
membership.

## Decisions

- Tenant roles are distinct from global platform roles.
- A user may belong to multiple organizations concurrently.

## Constraints

- Each active user-organization pair has at most one membership.
- Removing a membership invalidates its tenant authorization immediately.

## Open questions

- Can invitations be accepted by an authenticated user whose email differs
  from the invited address after verification?
- Are custom tenant roles required, or are owner, administrator, and member
  sufficient?

## Relationships

- [Token lifecycle](token-lifecycle.md)
- [Persistence](persistence.md)

