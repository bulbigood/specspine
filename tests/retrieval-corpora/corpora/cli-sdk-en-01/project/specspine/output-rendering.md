# Output rendering

**ID:** `output-rendering` · **Kind:** `concept`

Owns the durable architectural concept `output-rendering`.

## Responsibility

This document owns human and machine output.

## Modes

Interactive terminals receive concise text and progress updates. JSON mode
emits exactly one versioned envelope on standard output; progress and
diagnostics go to standard error. Fields are never omitted based on terminal
width. Quiet mode suppresses successful human output but not machine output.

Migration plans, plugin loading, cached reads, configuration inspection, and
rollback commands all use the same renderer. Their domain documents own the
meaning of fields; this document owns framing and streams.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Error contract](error-contract.md) | Provides neighboring architectural context |
| `related-to` | [Command dispatch](command-dispatch.md) | Provides neighboring architectural context |
| `related-to` | [Migration planning](migration-planning.md) | Provides neighboring architectural context |
