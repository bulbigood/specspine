# Configuration

## Responsibility

Configuration defines validated startup settings, secret references, dynamic
operational flags, and environment-specific defaults.

## Rules

Database credentials, payment credentials, carrier tokens, and webhook signing
material come from the secret store. Logs expose whether a value is present,
never its contents. Runtime changes are audited and converge across API and
worker processes.

Retry delay defaults are configurable within safety bounds, but
[Retry policy](retry-policy.md) owns their meaning. Incident controls can pause
one carrier or callback endpoint.

## Relationships

- [Observability](observability.md)
- [Incident response](incident-response.md)
