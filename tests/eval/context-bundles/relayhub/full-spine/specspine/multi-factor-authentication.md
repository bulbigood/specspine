# Multi-factor authentication

Multi-factor authentication adds a second proof to sensitive human authentication and account recovery.

## Responsibility

It owns factor enrollment, challenge state, recovery codes, factor removal, and policies that require a verified factor before a session or sensitive operation proceeds.

## Boundaries

- Primary credential proof belongs to [authentication](authentication.md).
- Session creation belongs to [login sessions](login-sessions.md).
- Enterprise identity requirements may be supplied by [enterprise SSO](enterprise-sso.md).

## Behavior

Enrollment requires a recent authenticated session and confirmation of the new factor. Challenges are short-lived and single-use. Recovery codes are disclosed once and consumed atomically. Removing the final factor requires step-up proof.

## Constraints

- Factor secrets and unused recovery codes are stored as non-recoverable verification material where possible.
- A partially completed challenge grants no application session or tenant authority.

## Open questions

- Which factor types and organization-enforced policies are supported initially?


