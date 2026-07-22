# External rate limits

External rate limits coordinate provider quotas across concurrent actions and polling work that share a connection or provider account.

## Responsibility

This capability owns quota buckets, observed provider limits, reservations, throttling delays, and propagation of retry timing.

## Boundaries

- RelayHub tenant product quotas belong to [usage quotas](usage-quotas.md).
- Provider operations belong to [connector actions](connector-actions.md).
- Scheduling delayed attempts belongs to [background jobs](background-jobs.md).

## Behavior

Before a provider call, the runtime reserves capacity against the most specific known bucket. Provider responses update remaining capacity and reset time. Exhausted capacity delays eligible work rather than causing an immediate terminal failure; interactive deadlines may return a normalized throttled outcome.

## Constraints

- Coordination is shared across workers so horizontal scaling cannot multiply permitted provider traffic.
- Provider-supplied retry timing takes precedence over locally estimated recovery.


