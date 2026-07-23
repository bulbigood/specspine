# Rate limits

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

- [HTTP request pipeline](http-request-pipeline.md)
- [Configuration](configuration.md)
