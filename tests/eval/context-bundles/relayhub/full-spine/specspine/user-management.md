# User management

User management owns user identity records and the API operations that create,
query, read, update, and delete them.

## Responsibility

It enforces unique normalized email addresses, password quality and hashing,
roles, verification state, paginated discovery, and user lifecycle mutations.

## Boundaries

- Credential proof and recovery belong to
  [authentication](authentication.md).
- Route authorization belongs to [access control](access-control.md).
- Generic model serialization and pagination mechanics belong to
  [persistence](persistence.md).
- Tenant participation and tenant roles belong to
  [organization membership](organization-membership.md); deleting a global
  user does not transfer organization ownership implicitly.

## Data ownership

A user record owns name, normalized unique email, password hash, role, email
verification state, and persistence timestamps. Passwords are private in JSON
serialization and are hashed before save when changed.

## Behavior

- Public registration creates a user without accepting an elevated role.
- Administrative creation accepts a declared `user` or `admin` role.
- Collection queries filter by name and role and support sorting and page/limit
  pagination.
- Item reads, updates, and deletes are available to administrators or the
  targeted user through the access-control self-service rule.
- Updates reject duplicate email addresses and rehash changed passwords.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- Email uniqueness is checked in the service and also represented by a unique
  model field. Evidence: `src/services/user.service.js`,
  `src/models/user.model.js`.
- API serialization omits password and persistence metadata and exposes `id`
  instead of MongoDB `_id`. Evidence: `src/models/plugins/toJSON.plugin.js`,
  `tests/unit/models/user.model.test.js`.
- Integration tests cover administrator and self access, query pagination,
  duplicate email, validation, update, and deletion behavior. Evidence:
  `tests/integration/user.test.js`.

## Open questions

- Deleting a user does not visibly cascade to token records. The intended
  cleanup and orphan-token policy is not established.

## Relationships

- [Token lifecycle](token-lifecycle.md)
- [Request pipeline](request-pipeline.md)

