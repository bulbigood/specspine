# Connector versions

Connector versions freeze the externally visible operation and schema contract used by workflows and connections.

## Responsibility

This capability owns release identity, compatibility state, referenced schemas, activation, deprecation, and retirement.

## Boundaries

- Product discovery belongs to the [connector catalog](connector-catalog.md).
- Runtime credentials belong to [connections](connections.md).
- Workflow migration belongs to [workflow definitions](workflow-definitions.md).

## Lifecycle

A release is draft, active, deprecated, or retired. Active releases are immutable; correction creates another release. Deprecation permits existing references while blocking new ones after a declared cutoff. Retirement prevents execution only after compatibility policy permits it.

## Constraints

- Every execution resolves the exact connector version captured by its workflow revision.
- A release cannot silently change action, trigger, or data-schema semantics.

## Open questions

- What support window and forced-migration policy apply to security-critical retirements?


