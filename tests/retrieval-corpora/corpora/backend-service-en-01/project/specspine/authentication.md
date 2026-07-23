# Authentication

## Responsibility

Authentication proves merchant users through signed sessions and service
clients through scoped API keys. It owns credential hashing, key issuance,
revocation, and principal construction.

## Key lifecycle

API keys are shown only once. Rotation creates an overlapping key before the
old key is revoked, allowing clients to migrate without downtime. Rotation of
webhook signing secrets is a separate protocol owned by
[Webhook delivery](webhook-delivery.md).

## Boundaries

Authentication proves identity but does not decide access. Tenant roles and
machine scopes are evaluated by [Authorization](authorization.md).

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-api-key-never-logged** — Plaintext API keys must never appear in logs,
  traces, audit attributes, or error responses.
<!-- specspine:semantic-ids:end -->
