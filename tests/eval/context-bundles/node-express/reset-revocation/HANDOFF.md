# Architecture context handoff

## Change intent

Invalidate all refresh and reset-password tokens after a successful password reset.

## Primary specification

`specspine/authentication.md`

## Required specifications

- `specspine/tokens.md`

## Architectural decisions and constraints

- Authentication orchestrates the reset workflow.
- Preserve `CON-token-ownership` from `specspine/tokens.md`: token persistence and bulk revocation stay inside the token capability.

## Relevant observations

Existing reset cleanup performs token persistence outside the canonical owner; do not copy that ownership conflict.

## Expected architectural outcome

A successful reset revokes both refresh and reset-password tokens through the token capability.
