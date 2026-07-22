# Execution concurrency

Execution concurrency admits workflow and step work without exceeding tenant, workflow, connection, or platform capacity.

## Responsibility

It owns concurrency keys, limits, distributed permits, queue ordering, permit expiry, and fair admission.

## Boundaries

- Commercial limits belong to [usage quotas](usage-quotas.md).
- Provider quotas belong to [external rate limits](external-rate-limits.md).
- Work lifecycle belongs to [workflow executions](workflow-executions.md) and [step executions](step-executions.md).

## Behavior

Queued work acquires every applicable permit before running. Expired worker leases release permits. Tenant isolation prevents one organization's backlog from consuming all shared capacity; higher service tiers may receive different limits without bypassing hard platform safety ceilings.

## Constraints

- Permit accounting is coordinated across workers and recoverable after process loss.
- Lower concurrency changes delay work but do not change execution semantics.


