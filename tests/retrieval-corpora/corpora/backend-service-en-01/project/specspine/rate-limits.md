# Rate limits

**ID:** `rate-limits` · **Kind:** `concept`

**Summary:** Owns the durable architectural concept `rate-limits`.

## Responsibility

Rate limits protect public API capacity and apply fair tenant budgets to
expensive operations.

## Behavior

Limits are evaluated after authentication and before capability handlers.
Responses include a retry-after hint, but clients must still apply jitter to
avoid coordinated traffic. Merchant API throttling does not define carrier
provider quotas or background-job attempt budgets.

Administrative reads and status callbacks have separate buckets. Emergency
configuration can lower a tenant budget without restarting the API.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [HTTP request pipeline](http-request-pipeline.md) | Provides neighboring architectural context |
| `related-to` | [Configuration](configuration.md) | Provides neighboring architectural context |
