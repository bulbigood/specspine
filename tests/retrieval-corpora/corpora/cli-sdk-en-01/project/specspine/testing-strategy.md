# Testing strategy

**ID:** `testing-strategy` · **Kind:** `concept`

Owns the durable architectural concept `testing-strategy`.

## Responsibility

This guide defines confidence layers for AtlasForge changes.

## Layers

Unit tests cover parsing, configuration merges, profile inheritance, migration
ordering, lease generations, plugin ranges, renderers, caches, telemetry
redaction, and exit-code mapping. Contract tests run SDK implementations
against shared fixtures. End-to-end tests invoke the binary with disposable
databases and isolated home directories.

Clock-controlled tests exercise expired leases and renewals. Golden files
cover JSON output. Compatibility fixtures retain older manifests and plugins.
Tests describe many policies but do not own their production semantics.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Configuration resolution](configuration-resolution.md) | Provides neighboring architectural context |
| `related-to` | [Migration locking](migration-locking.md) | Provides neighboring architectural context |
| `related-to` | [Plugin API](plugin-api.md) | Provides neighboring architectural context |
| `related-to` | [Output rendering](output-rendering.md) | Provides neighboring architectural context |
