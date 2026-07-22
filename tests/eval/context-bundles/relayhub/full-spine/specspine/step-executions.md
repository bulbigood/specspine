# Step executions

Step executions track every durable attempt to perform one action in a workflow execution.

## Responsibility

They own dependency readiness, rendered input, attempt identity, lease, deadline, sanitized output, failure class, and completion evidence.

## Boundaries

- Action contracts belong to [connector actions](connector-actions.md).
- Retry policy belongs to [execution retries](execution-retries.md).
- Run-level state belongs to [workflow executions](workflow-executions.md).
- Provider throttling belongs to [external rate limits](external-rate-limits.md).

## Behavior

A ready step obtains concurrency capacity and a lease before invoking its pinned connector action. Lease expiry makes interrupted work recoverable. Completion makes dependent steps eligible. Cancellation prevents new attempts and asks interruptible adapters to stop without assuming external side effects were rolled back.

## Constraints

- Durable inputs and outputs exclude credentials and provider-sensitive error bodies.
- Repeated attempts preserve a stable operation identity for idempotent provider calls.


