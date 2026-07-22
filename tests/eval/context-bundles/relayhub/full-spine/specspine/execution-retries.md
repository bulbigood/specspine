# Execution retries

Execution retries decide whether and when a failed step attempt may run again.

## Responsibility

They own failure classification, attempt ceilings, backoff, retry deadlines, manual retry eligibility, and exhaustion disposition.

## Boundaries

- Provider error normalization belongs to [connector actions](connector-actions.md).
- Attempt records belong to [step executions](step-executions.md).
- Exhausted work ownership belongs to [dead-letter handling](dead-letter-handling.md).

## Behavior

Transport interruption, provider unavailability, and throttling are retryable within policy. Invalid input, missing authorization, and deterministic provider rejection pause or fail without blind repetition. Retry scheduling preserves execution and operation identities while creating a distinct attempt.

## Constraints

- Retry cannot exceed the workflow's overall deadline or tenant quota policy.
- Unknown failures default to bounded recovery, never unbounded immediate retry.


