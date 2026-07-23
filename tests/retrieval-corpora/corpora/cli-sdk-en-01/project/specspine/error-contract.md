# Error contract

## Responsibility

This document owns stable exit statuses and structured diagnostics.

## Mapping

Usage and configuration failures exit with status 2. Connectivity failures use
3, migration conflicts use 4, plugin incompatibilities use 5, and unexpected
internal failures use 70. Cancellation uses 130 only when initiated by an
interrupt signal.

JSON diagnostics contain a stable code, public message, optional remediation,
and correlation ID. Causes and stack traces are sent only to debug logs.
Commands may describe errors, but they do not allocate exit statuses.

## Relationships

- [Output rendering](output-rendering.md)
- [Command dispatch](command-dispatch.md)
- [Plugin API](plugin-api.md)
