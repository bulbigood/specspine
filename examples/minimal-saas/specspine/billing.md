# Billing

Owns subscription state and synchronizes it with an external payment provider.

## Responsibility

- create and change subscriptions;
- process payment-provider events;
- expose the current subscription state;
- preserve provider identifiers required for synchronization.

## Boundaries

Billing does not authenticate users or own organization membership.

## Behavior

Provider events may be received more than once and must not apply the same
state transition twice.

## Relationships

### Used by

- [Application](application.md)

### Depends on

- [Operations](operations.md)

## Decisions

- The local subscription record is the application's current view of billing
  state.
- **DEC-idempotent-provider-events** — Payment-provider event handling must be
  idempotent.

## Open questions

- Which provider is used initially?
- How are failed or delayed provider events reconciled?
