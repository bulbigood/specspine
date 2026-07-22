# Service health

Service health exposes whether RelayHub API and workers can safely accept or execute work.

## Responsibility

It owns liveness, readiness, dependency health, worker heartbeat, degraded-state classification, and safe operational status interfaces.

## Boundaries

- Process lifecycle belongs to [configuration and operations](configuration-operations.md).
- Tenant-visible disruption belongs to [incident management](incident-management.md).
- Individual execution failures remain with [workflow executions](workflow-executions.md).

## Interfaces

Liveness reports process viability without dependency calls. Readiness verifies required durable dependencies and refuses new traffic when safe operation is impossible. Worker heartbeats expose aggregate capacity without tenant data or secrets.

## Constraints

- Health endpoints require no tenant authentication but reveal no configuration, credentials, internal addresses, or customer identifiers.
- A degraded optional channel does not mark unrelated execution paths unavailable.


