# Idempotency

Idempotency gives retryable mutation requests and asynchronous handlers one
stable operation identity, preventing repeated execution from duplicating
business effects.

## Responsibility

It owns idempotency-key scope, request fingerprinting, in-progress ownership,
completed-result replay, conflict detection, expiry, and safe recovery after an
interrupted attempt.

## Boundaries

- Each capability decides which mutations support or require idempotency.
- [Request pipeline](request-pipeline.md) transports client keys but does not
  own their business scope.
- [Background jobs](background-jobs.md) and
  [event delivery](event-delivery.md) provide stable delivery identities used
  by asynchronous handlers.
- Persistence owns atomic storage mechanisms, not operation semantics.

## Interfaces

Retryable HTTP mutations accept `Idempotency-Key`. The effective identity is
scoped by organization, authenticated principal, operation type, and key. A
repeated matching request returns the recorded outcome; reuse with a different
request fingerprint returns a conflict.

Asynchronous handlers use job or event identity instead of accepting a new
caller-provided key.

## Lifecycle

An idempotency record is executing, completed, or recoverable after its owner
lease expires. Completed outcomes remain replayable for the capability's
declared retry window and expire only after duplicate delivery is no longer
expected.

<!-- specspine:semantic-ids:begin -->
## Decisions

- **DEC-idempotency-scope** — Client keys are isolated by organization,
  principal, and operation rather than being globally unique.

## Constraints

- **CON-idempotent-atomic-effect** — Recording completion and committing the
  protected business effect must form one recoverable atomic boundary.
<!-- specspine:semantic-ids:end -->

## Open questions

- Which endpoint classes require keys rather than merely supporting them?
- May replay return the exact original response after the caller's permissions
  have changed?

## Relationships

- [Organizations](organizations.md)
- [API credentials](api-credentials.md)

