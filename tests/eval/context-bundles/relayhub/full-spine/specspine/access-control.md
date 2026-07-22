# Access control

Access control turns a bearer credential into a current principal and enforces
global or organization-scoped permissions.

## Responsibility

It validates access-purpose JWTs through Passport, resolves the subject to a
current user record, attaches that user to the request, and checks required
rights against the configured role map.

For tenant-scoped operations it also resolves active
[organization membership](organization-membership.md) and evaluates the
membership role inside the explicitly selected [organization](organizations.md).
Machine requests instead resolve a [service account](service-accounts.md) from
an [API credential](api-credentials.md) and evaluate its granted scopes.

## Boundaries

- Issuing and rotating tokens belongs to the
  [token lifecycle](token-lifecycle.md).
- User roles are stored with [user management](user-management.md), while this
  boundary interprets roles as rights.
- HTTP failure serialization belongs to the
  [request pipeline](request-pipeline.md).
- Exceptional platform assistance belongs to [support access](support-access.md)
  and never follows from a standing platform role.

## Behavior

- Missing, invalid, wrong-purpose, or orphaned access tokens result in an
  unauthorized failure.
- A protected route may require zero or more rights; all listed rights must be
  present.
- When required rights are absent, access is still allowed if the route's
  `userId` parameter equals the authenticated user's id.
- Administrative user collection operations require configured rights; user
  item operations therefore support both administrators and the matching user.
- Organization-scoped authorization requires both an authenticated identity
  and active membership in the requested tenant.
- Global platform roles never implicitly grant tenant membership.
- Human permissions and service-account scopes are separate authorization
  vocabularies and cannot be substituted for each other.

## Interfaces

The role map currently gives `admin` the `getUsers` and `manageUsers` rights;
`user` has no named rights. Routes declare rights by passing those names to the
authentication middleware.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- Access JWT verification rejects every token type except `access` and performs
  a user lookup for every authenticated request. Evidence:
  `src/config/passport.js`.
- The self-service exception depends specifically on a `userId` route
  parameter. Evidence: `src/middlewares/auth.js`,
  `tests/integration/user.test.js`.

## Open questions

- The self-service exception applies whenever a protected route has a matching
  `userId`, independent of which named right was requested. The repository does
  not state whether this broad coupling is intentional for future routes.

## Relationships

- [Authentication](authentication.md)
- [API runtime](api-runtime.md)

