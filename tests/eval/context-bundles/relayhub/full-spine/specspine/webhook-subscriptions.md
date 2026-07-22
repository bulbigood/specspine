# Webhook subscriptions

Webhook subscriptions let an organization select domain events for delivery
to a verified HTTPS endpoint.

## Responsibility

This capability owns subscription configuration, endpoint verification,
event-type selection, signing secrets, delivery attempts, retry disposition,
disablement, and tenant-visible delivery history.

## Boundaries

- Event identity and internal publication belong to
  [event delivery](event-delivery.md).
- Retry execution belongs to [background jobs](background-jobs.md), while this
  capability owns webhook-specific retry policy.
- Tenant ownership belongs to [organizations](organizations.md).
- Secret disclosure follows the one-time handling principle defined for
  [API credentials](api-credentials.md), but webhook secrets are not client
  authentication credentials.

## Interfaces

- `POST /v1/organizations/{organizationId}/webhook-subscriptions` creates a
  disabled subscription and returns its signing secret once.
- `POST /v1/organizations/{organizationId}/webhook-subscriptions/{subscriptionId}/verify`
  initiates endpoint ownership verification.
- `GET /v1/organizations/{organizationId}/webhook-subscriptions` lists safe
  configuration and status.
- `PATCH /v1/organizations/{organizationId}/webhook-subscriptions/{subscriptionId}`
  changes endpoint or selected event types and requires reverification when
  endpoint identity changes.
- `DELETE /v1/organizations/{organizationId}/webhook-subscriptions/{subscriptionId}`
  disables future delivery.
- `GET /v1/organizations/{organizationId}/webhook-deliveries/{deliveryId}`
  exposes attempt status without disclosing signing secrets.

## Delivery behavior

Each request carries event identity, payload version, delivery attempt, and a
signature over the exact transmitted bytes. Success requires an accepted HTTP
status before the attempt deadline. Retryable transport or server failures use
bounded delayed retries; persistent failures disable the subscription and
remain visible to tenant administrators.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-webhook-stable-event-id** — Redelivery preserves the original event
  identifier so receivers can deduplicate effects.
- **CON-webhook-secret-nondisclosure** — Signing secrets are never returned by
  read or delivery-history interfaces after creation.
<!-- specspine:semantic-ids:end -->

## Open questions

- Which response statuses are terminal rather than retryable?
- What retry horizon and delivery-history retention are required?

## Relationships

- [Access control](access-control.md)
- [Audit log](audit-log.md)

