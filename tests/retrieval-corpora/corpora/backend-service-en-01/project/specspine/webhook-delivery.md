# Webhook delivery

## Responsibility

Webhook delivery owns merchant callback subscriptions, payload signing,
delivery attempts, and endpoint health.

## Signature verification

Every callback carries a timestamp and an HMAC signature over the exact body.
The signing secret is tenant-specific. Consumers reject stale timestamps
before comparing signatures in constant time.

## Secret rotation

Rotation creates a new signing key while retaining the previous secret for a
bounded overlap window. During overlap, callbacks include the active key
identifier so receivers can select either secret. After the window, the old
key is destroyed and can no longer sign deliveries.

Delivery retries use the shared scheduling policy, but this document owns the
callback attempt history and endpoint suspension threshold.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-webhook-secret-overlap** — Signing-secret rotation must provide a
  bounded two-key verification window.
<!-- specspine:semantic-ids:end -->

## Relationships

- [Retry policy](retry-policy.md)
- [Background jobs](background-jobs.md)
- [Authentication](authentication.md)
