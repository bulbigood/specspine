# Output rendering

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

- [Error contract](error-contract.md)
- [Command dispatch](command-dispatch.md)
- [Migration planning](migration-planning.md)
