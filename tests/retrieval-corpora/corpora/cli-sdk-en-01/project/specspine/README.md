# AtlasForge CLI and SDK

## Purpose

AtlasForge is a command-line database migration client with an embeddable SDK.
It resolves layered configuration, plans local migration files, coordinates
locks, loads optional plugins, and renders stable machine-readable output.

## Architecture map

### Invocation and configuration

- [Command dispatch](command-dispatch.md) owns command parsing and execution boundaries.
- [Configuration resolution](configuration-resolution.md) owns source precedence and explicit unsetting.
- [Profile inheritance](profile-inheritance.md) owns named profile composition.
- [Credential store](credential-store.md) owns secret lookup and redaction.

### Migration lifecycle

- [Migration planning](migration-planning.md) owns discovery, ordering, and dry-run plans.
- [Migration locking](migration-locking.md) owns leases and stale-lock recovery.
- [Rollback policy](rollback-policy.md) owns reversal eligibility and partial failures.
- [Local cache](local-cache.md) owns downloaded metadata and offline reads.

### Extension and interface

- [Plugin API](plugin-api.md) owns extension discovery and compatibility.
- [Output rendering](output-rendering.md) owns terminal and structured output.
- [Error contract](error-contract.md) owns exit codes and diagnostic envelopes.
- [Release compatibility](release-compatibility.md) owns CLI, SDK, and plugin version support.

### Operations

- [Telemetry](telemetry.md) owns anonymous usage events and opt-out behavior.
- [Testing strategy](testing-strategy.md) defines test layers and fixtures.

## System shape

The CLI parses intent before the SDK resolves configuration. Planning is
side-effect free; application acquires a renewable lease. Plugins may add
commands and migration readers but cannot replace locking or credential rules.
