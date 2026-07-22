# Connector catalog

The connector catalog describes the external systems RelayHub can integrate with and the capabilities each connector exposes.

## Responsibility

It owns connector identity, publisher, lifecycle status, supported authentication families, and navigation to versioned triggers and actions.

## Boundaries

- Immutable releases belong to [connector versions](connector-versions.md).
- Tenant-specific authorization belongs to [connections](connections.md).
- Executable operations belong to [connector actions](connector-actions.md) and [connector triggers](connector-triggers.md).

## Interfaces

Users and workflow tooling can list and inspect available connectors, versions, authentication requirements, triggers, and actions. Disabled catalog entries remain resolvable by existing workflows but cannot be selected for new configuration.

## Decisions

- Connector identity is stable across release versions and independent of tenant connections.

## Open questions

- Are connectors published only by RelayHub, or can vetted partners own catalog entries?


