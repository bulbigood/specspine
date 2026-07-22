# Connections

Connections are tenant-owned authorizations that let connector operations access one external account or installation.

## Responsibility

They own tenant association, connector identity and version compatibility, display metadata, authorization method, health state, and revocation.

## Boundaries

- OAuth authorization belongs to [OAuth connections](oauth-connections.md).
- Static secrets belong to [external API credentials](external-api-credentials.md) and [credential vault](credential-vault.md).
- Executions consume connections through [connector actions](connector-actions.md) or [connector triggers](connector-triggers.md).

## Interfaces

Tenant administrators create, inspect, rename, reconnect, test, and disable connections. Read interfaces expose health and granted external identity but never secret material.

## Lifecycle

A connection is pending, active, degraded, authorization-required, disabled, or revoked. Disabling blocks new external calls while preserving workflow configuration and execution history.

## Constraints

- A connection belongs to exactly one organization and cannot be referenced across tenant boundaries.


