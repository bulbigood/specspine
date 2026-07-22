# Data retention

Data retention applies lifecycle and deletion policy to tenant configuration, execution history, audit evidence, usage, and secrets.

## Responsibility

It owns retention classes, expiry calculation, legal or support holds, deletion scheduling, anonymization boundaries, and deletion evidence.

## Boundaries

- Each capability remains owner of record meaning and active-state deletion constraints.
- Organization closure belongs to [organizations](organizations.md).
- Commercial retention tier belongs to [plans and entitlements](plans-entitlements.md).
- Immutable security evidence belongs to [audit log](audit-log.md).

## Behavior

Expiry creates idempotent cleanup work after applicable holds and minimum retention are evaluated. Closing a tenant blocks new activity, revokes secrets, and schedules capability-specific cleanup; it does not imply immediate erasure of legally retained billing or audit records.

## Constraints

- Cleanup cannot leave recoverable plaintext secrets or cross-tenant references.
- Retention shortening applies prospectively subject to mandatory minimums.


