# Credential store

**ID:** `credential-store` · **Kind:** `concept`

**Summary:** Owns the durable architectural concept `credential-store`.

## Responsibility

This document owns lookup and handling of database credentials.

## Rules

Configuration contains credential references, not secret material. References
may address the operating-system keychain or a process-scoped environment
provider. Resolution occurs after source precedence and before connection
creation. Missing references are fatal.

Secret values are tagged in memory so configuration inspection, telemetry,
errors, and debug logs redact them. Credentials are never persisted in the
local cache.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Configuration resolution](configuration-resolution.md) | Provides neighboring architectural context |
| `related-to` | [Local cache](local-cache.md) | Provides neighboring architectural context |
| `related-to` | [Telemetry](telemetry.md) | Provides neighboring architectural context |
