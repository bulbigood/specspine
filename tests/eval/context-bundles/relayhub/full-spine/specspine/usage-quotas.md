# Usage quotas

Usage quotas enforce tenant and platform safety limits before accepting or running integration work.

## Responsibility

They own effective limits, reservation and consumption counters, enforcement windows, overage policy, and rejection evidence.

## Boundaries

- Commercial grants belong to [plans and entitlements](plans-entitlements.md).
- Billable recording belongs to [usage metering](usage-metering.md).
- Parallel execution control belongs to [execution concurrency](execution-concurrency.md).
- Provider quotas belong to [external rate limits](external-rate-limits.md).

## Behavior

Admission checks resolve the current entitlement and any platform safety ceiling. Hard exhaustion rejects or delays new work with reset information; soft limits continue while emitting usage and notification signals. Reservations expire after abandoned work.

## Constraints

- Quota checks and accepted reservations are coordinated across API and workers.
- Administrative override is bounded, time-limited, and audited.


