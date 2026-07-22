# Token lifecycle

Token lifecycle owns the distinct JWT purposes used by authentication and the
durable records that make non-access tokens revocable and consumable.

## Responsibility

It signs purpose-tagged JWTs, determines their expiry, persists refresh/reset/
verification token records, verifies both signature and matching active
record, and returns access/refresh pairs.

## Boundaries

- Credential proof and purpose-level flows belong to
  [authentication](authentication.md).
- Protected-request access-token verification belongs to
  [access control](access-control.md).
- Token record structure and MongoDB ownership belong to
  [persistence](persistence.md).

## Token categories

- Access tokens are signed JWTs with user subject, expiry, and `access` type;
  they are not persisted.
- Refresh tokens are persisted and checked for type, user, and blacklist state.
- Reset-password and verify-email tokens use the same persisted-token mechanism
  with separate purpose tags and shorter configurable lifetimes.

## Behavior

JWT verification alone is insufficient for persisted token types: a matching,
non-blacklisted token record must also exist. Access authentication instead
validates JWT type and resolves the current user directly.

## Data ownership

The token record owns the complete token string, user reference, purpose,
expiry, blacklist flag, and timestamps. The observed flows remove records to
consume or revoke tokens; they do not set the blacklist flag.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- One shared secret signs every token purpose. Evidence:
  `src/services/token.service.js`, `src/config/config.js`.
- Access expiry is measured in minutes, refresh in days, and reset/verification
  in minutes. Evidence: `src/config/config.js`.
- Persisted-token lookup checks the full token string, type, subject, and
  blacklist state. Evidence: `src/services/token.service.js`,
  `src/models/token.model.js`.

## Open questions

- The repository does not establish a retention or cleanup mechanism for
  expired token records.
- The persisted `blacklisted` field has no observed mutation path; its intended
  use relative to record deletion is unclear.

