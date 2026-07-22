# Execution replay

Execution replay creates a new workflow execution from selected historical evidence after failure or operator diagnosis.

## Responsibility

It owns replay authorization, source selection, input snapshot, revision choice, connection revalidation, linkage, and replay scope.

## Boundaries

- Historical state belongs to [workflow executions](workflow-executions.md) and [dead-letter handling](dead-letter-handling.md).
- Definition versions belong to [workflow definitions](workflow-definitions.md).
- New step attempts belong to [step executions](step-executions.md).

## Behavior

An operator may replay an entire terminal execution or resume from an eligible failed step. Replay validates current authorization, connections, entitlements, and retained inputs. It creates a new execution with a link to the source and never changes the source history.

## Constraints

- Replay is an auditable mutation and cannot silently reuse expired credentials or cross an environment boundary.
- Billing and idempotency distinguish replayed computation from duplicate technical delivery.


