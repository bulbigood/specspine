# Authentication

Owns registration, login, logout, password reset, and email verification workflows.

Authentication orchestrates password reset and delegates token persistence and bulk revocation to [Tokens](tokens.md).

## Constraints

A successful password reset invalidates every refresh token and reset-password token belonging to that user.
