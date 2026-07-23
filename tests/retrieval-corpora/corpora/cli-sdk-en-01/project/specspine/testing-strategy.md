# Testing strategy

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

- [Configuration resolution](configuration-resolution.md)
- [Migration locking](migration-locking.md)
- [Plugin API](plugin-api.md)
- [Output rendering](output-rendering.md)
