# Rollback policy

## Responsibility

This document owns whether and how applied migrations can be reversed.

## Rules

Only a migration with an explicit down step is reversible. Rollbacks execute
in reverse dependency order under the same exclusive lease used by forward
application. A failed down step stops the sequence; previously reversed steps
remain recorded and are not automatically replayed.

The `--force` flag bypasses the clean-working-tree check but never bypasses
lease ownership, checksum validation, or irreversibility.

## Relationships

- [Migration locking](migration-locking.md)
- [Migration planning](migration-planning.md)
- [Error contract](error-contract.md)
