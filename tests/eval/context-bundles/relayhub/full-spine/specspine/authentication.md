# Authentication

Authentication owns account registration, password login, logout, password
recovery, and email verification orchestration.

## Responsibility

It proves credentials against a user record and coordinates identity-related
state changes with token issuance, token consumption, and email delivery.

## Boundaries

- JWT creation, persistence, and verification belong to the
  [token lifecycle](token-lifecycle.md).
- Bearer authentication for protected requests belongs to
  [access control](access-control.md).
- User record validation and mutation belong to
  [user management](user-management.md).
- Message transport belongs to [email delivery](email-delivery.md).

## Behavior

- Registration creates a default-role user and returns access and refresh
  tokens.
- Login compares the supplied password with the stored hash and returns the
  user plus a new token pair.
- Logout removes the matching active refresh-token record.
- Refresh consumes the presented refresh token before issuing a replacement
  pair.
- Password recovery creates a reset token and emails a link; reset consumes
  the logical reset-token set after changing the password.
- Verification creates and emails a token; successful verification removes
  verification tokens and marks the user verified.

## Failure behavior

Invalid login credentials return one undifferentiated unauthorized failure.
Invalid refresh, reset, and verification flows are translated to purpose-level
authentication errors rather than exposing lower-level JWT or persistence
failures.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- Password authentication uses email lookup followed by bcrypt comparison.
  Evidence: `src/services/auth.service.js`, `src/models/user.model.js`.
- Refresh is single-use in the normal flow because its persisted record is
  removed before replacement tokens are generated. Evidence:
  `src/services/auth.service.js`, `tests/integration/auth.test.js`.
- Password-reset and verification operations delete all persisted tokens of
  the consumed type for that user. Evidence: `src/services/auth.service.js`.

## Open questions

- No explicit policy states whether changing a password should revoke existing
  refresh tokens; observed code only removes reset tokens.
- Email verification state is stored but is not required by observed login or
  authorization paths. Whether unverified accounts should be restricted is
  unresolved.

## Relationships

- [Persistence](persistence.md)
- [Request pipeline](request-pipeline.md)

