# Login sessions

Login sessions represent revocable human access across devices after an identity method has been proven.

## Responsibility

This capability owns session identity, device metadata, refresh rotation, idle and absolute expiry, session listing, and individual or account-wide revocation.

## Boundaries

- Credential proof belongs to [authentication](authentication.md), [external identity](external-identity.md), or [enterprise SSO](enterprise-sso.md).
- Step-up challenges and enrolled factors belong to
  [multi-factor authentication](multi-factor-authentication.md).
- Token encoding belongs to [token lifecycle](token-lifecycle.md).
- Tenant authorization is evaluated by [access control](access-control.md).

## Interfaces

Login creates a session and returns a short-lived access token plus rotating refresh credential. Authenticated users can list and revoke their sessions; password reset and account disablement can revoke every session.

## Constraints

- Refresh reuse terminates the affected session rather than creating another valid token chain.
- Session records never contain third-party provider access tokens.

## Open questions

- Which risk signals require reauthentication or global revocation?

