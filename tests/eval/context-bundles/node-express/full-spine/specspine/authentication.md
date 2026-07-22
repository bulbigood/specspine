# Authentication

Owns identity-establishing workflows including registration, login, logout, password reset, and email verification.

Authentication orchestrates user and token capabilities but does not own token persistence or role policy.

## Constraints

- A successful password reset invalidates every refresh token and every reset-password token belonging to that user.
- Authentication delegates token persistence and bulk revocation to [Tokens](tokens.md).

## Observed

<!-- specspine:evidence-baseline source=179ae84efec61b14206d0305d941daed6c6d07f9; inspected=2026-07-22 -->

- Existing reset-password cleanup performs a token-storage operation outside the canonical token owner. This observation does not override the accepted ownership boundary.

## Relationships

- [Tokens](tokens.md)
- [Users](users.md)
- [Email delivery](email.md)
