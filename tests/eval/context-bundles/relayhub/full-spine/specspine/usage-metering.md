# Usage metering

Usage metering records billable consumption produced by workflow and connector activity.

## Responsibility

It owns meter identity, immutable usage events, quantity, tenant and billing dimensions, correction, aggregation, and provider reporting progress.

## Boundaries

- Execution facts belong to [workflow executions](workflow-executions.md).
- Enforcement belongs to [usage quotas](usage-quotas.md).
- Pricing and included quantities belong to [plans and entitlements](plans-entitlements.md).
- Invoice presentation belongs to [invoices](invoices.md).

## Behavior

Accepted execution milestones emit deduplicated usage events using stable source identities. Aggregation groups events into billing periods without destroying raw evidence. Corrections append compensating events. Provider reporting is retryable and checkpointed.

## Constraints

- Replayed or retried technical work cannot create duplicate billable usage for the same logical event.
- Aggregates are reproducible from retained usage events and corrections.


