# Release compatibility

## Responsibility

This document owns support windows across CLI, SDK, manifests, and plugins.

## Policy

The CLI and SDK follow semantic versioning. A minor CLI release can read the
current and previous manifest schema. The plugin API has an independent major
version and is checked from each declared range before activation.

Deprecations remain for two minor releases and produce one warning per
invocation. Database ledger formats require an explicit upgrade command and
are never rewritten merely by inspecting a plan.

## Relationships

- [Plugin API](plugin-api.md)
- [Migration planning](migration-planning.md)
- [Command dispatch](command-dispatch.md)
