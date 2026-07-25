# Migration locking

**ID:** `migration-locking` · **Kind:** `concept`

Owns the durable architectural concept `migration-locking`.

## Responsibility

This short policy owns exclusive migration leases.

## Rules

Application acquires a lease before its first write and renews it at one third
of the lease duration. A contender may reclaim an expired lease only after a
database-time comparison and a successful compare-and-swap on the lease
generation. Wall-clock time from the CLI host is never authoritative. Release
is best effort after the transaction finishes.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Migration planning](migration-planning.md) | Provides neighboring architectural context |
| `related-to` | [Rollback policy](rollback-policy.md) | Provides neighboring architectural context |
