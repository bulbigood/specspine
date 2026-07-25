# Observability

**ID:** `observability` · **Kind:** `concept`

Owns the durable architectural concept `observability`.

## Responsibility

Observability defines structured logs, metrics, traces, correlation fields,
redaction, and service-level indicators.

## Signals

Requests and jobs propagate tenant, request, order, and operation identifiers.
Metrics report queue delay, provider latency, callback attempts, retry counts,
and payment outcomes. Dashboards separate transient failures from permanent
rejections.

Logs never include API keys, payment credentials, webhook secrets, full
addresses, or raw callback bodies. Sampling preserves all exhausted retries
and financial conflicts.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [HTTP request pipeline](http-request-pipeline.md) | Provides neighboring architectural context |
| `related-to` | [Background jobs](background-jobs.md) | Provides neighboring architectural context |
| `related-to` | [Incident response](incident-response.md) | Provides neighboring architectural context |
