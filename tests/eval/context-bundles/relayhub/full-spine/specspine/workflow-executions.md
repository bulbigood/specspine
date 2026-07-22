# Workflow executions

Workflow executions are durable instances of one immutable workflow revision started by one accepted trigger.

## Responsibility

They own run identity, tenant and environment context, trigger evidence, lifecycle, aggregate outputs, cancellation intent, and terminal disposition.

## Boundaries

- Definition ownership belongs to [workflow definitions](workflow-definitions.md).
- Individual work belongs to [step executions](step-executions.md).
- Parallelism admission belongs to [execution concurrency](execution-concurrency.md).
- Historical restart belongs to [execution replay](execution-replay.md).

## Lifecycle

An execution is queued, running, cancellation-requested, succeeded, failed, cancelled, or dead-lettered. Terminal state is derived from durable step outcomes and cannot be reopened; replay creates another linked execution.

## Interfaces

Tenant users can list, inspect, cancel, and when authorized replay executions. Responses expose sanitized inputs, outputs, timing, revision, and failure classification.


