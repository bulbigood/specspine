# Observability

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

- [HTTP request pipeline](http-request-pipeline.md)
- [Background jobs](background-jobs.md)
- [Incident response](incident-response.md)
