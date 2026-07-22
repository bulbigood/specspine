# Incident management

Incident management communicates platform disruptions and coordinates their customer-visible lifecycle.

## Responsibility

It owns incident identity, affected capabilities and regions, severity, status, public updates, organization impact association, and resolution summary.

## Boundaries

- Detection evidence belongs to [service health](service-health.md) and operational monitoring.
- Direct messages belong to [notification delivery](notification-delivery.md).
- Privileged tenant investigation belongs to [support access](support-access.md).

## Lifecycle

An incident is investigating, identified, monitoring, or resolved. Updates are append-only and time ordered. Tenant impact can be associated after detection without exposing another tenant's state.

## Constraints

- Incident communication contains no credentials, personal data, or tenant-specific payloads.
- Resolution does not rewrite execution history; affected work follows normal retry, replay, or dead-letter policy.


