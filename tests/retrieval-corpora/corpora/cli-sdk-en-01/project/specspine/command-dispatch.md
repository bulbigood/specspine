# Command dispatch

**ID:** `command-dispatch` · **Kind:** `concept`

**Summary:** Owns the durable architectural concept `command-dispatch`.

## Responsibility

This document owns argument parsing, command selection, and the boundary
between the executable and the embeddable SDK.

## Behavior

Global flags are parsed before plugin commands are discovered. A command
receives an immutable invocation containing the selected profile, output mode,
and cancellation signal. The dispatcher never resolves configuration values
or opens a database connection.

Long-running commands report progress through the renderer. Errors cross the
boundary as typed SDK errors, which the error contract maps to exit statuses.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Configuration resolution](configuration-resolution.md) | Provides neighboring architectural context |
| `related-to` | [Plugin API](plugin-api.md) | Provides neighboring architectural context |
| `related-to` | [Output rendering](output-rendering.md) | Provides neighboring architectural context |
| `related-to` | [Error contract](error-contract.md) | Provides neighboring architectural context |
