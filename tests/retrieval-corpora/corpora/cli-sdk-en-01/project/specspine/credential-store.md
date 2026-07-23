# Credential store

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

- [Configuration resolution](configuration-resolution.md)
- [Local cache](local-cache.md)
- [Telemetry](telemetry.md)
