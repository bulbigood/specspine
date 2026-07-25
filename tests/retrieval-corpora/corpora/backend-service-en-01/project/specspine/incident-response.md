# Incident response

**ID:** `incident-response` · **Kind:** `concept`

Owns the durable architectural concept `incident-response`.

## Responsibility

Incident response owns severity declaration, command roles, mitigation
tracking, merchant communication, and follow-up actions.

## Provider incidents

Operators may pause label purchase for one carrier, lower concurrency, or
suspend callbacks to an unhealthy merchant endpoint. Mitigation preserves
durable jobs and their attempt history. Recovery is gradual so retry traffic
does not overwhelm a provider.

## Evidence

Dashboards, structured logs, and traces provide technical evidence. Payment
and order records remain the business source of truth. Incident notes link to
configuration changes and record when normal limits are restored.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Observability](observability.md) | Provides neighboring architectural context |
| `related-to` | [Configuration](configuration.md) | Provides neighboring architectural context |
| `related-to` | [Retry policy](retry-policy.md) | Provides neighboring architectural context |
