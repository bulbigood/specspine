# Telemetry

## Responsibility

This document owns anonymous operational events emitted by the CLI.

## Rules

Telemetry is disabled when `ATLASFORGE_TELEMETRY=off` or the configuration
opt-out is true. The environment setting wins for emergency suppression.
Events include command family, duration bucket, result class, and host version.
They exclude arguments, paths, profile names, SQL, credentials, and output.

Performance profiling used during development is not a user configuration
profile and is never uploaded automatically.

## Relationships

- [Credential store](credential-store.md)
- [Profile inheritance](profile-inheritance.md)
- [Command dispatch](command-dispatch.md)
