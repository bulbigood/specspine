# Rollback policy

**ID:** `rollback-policy` · **Kind:** `concept`

**Summary:** Owns the durable architectural concept `rollback-policy`.

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

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Migration locking](migration-locking.md) | Provides neighboring architectural context |
| `related-to` | [Migration planning](migration-planning.md) | Provides neighboring architectural context |
| `related-to` | [Error contract](error-contract.md) | Provides neighboring architectural context |
