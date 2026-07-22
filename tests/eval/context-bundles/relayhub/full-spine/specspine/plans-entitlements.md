# Plans and entitlements

Plans and entitlements translate a commercial offering into capabilities and enforceable product limits.

## Responsibility

They own plan identity and version, feature grants, included usage, concurrency class, retention tier, and effective entitlement resolution.

## Boundaries

- Purchase lifecycle belongs to [subscriptions](subscriptions.md).
- Measured consumption belongs to [usage metering](usage-metering.md).
- Runtime enforcement belongs to [usage quotas](usage-quotas.md).

## Behavior

A subscription pins a plan version for its billing period. Effective entitlements combine that version with explicit, auditable overrides. Plan publication is immutable; price or grant changes create another version and do not silently alter existing contracts.

## Constraints

- Authorization never relies on display plan names or client-supplied entitlements.
- Loss of entitlement blocks new restricted work without deleting existing definitions or history.


