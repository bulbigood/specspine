# Migration planning

**ID:** `migration-planning` · **Kind:** `concept`

**Summary:** Owns the durable architectural concept `migration-planning`.

## Responsibility

This specification owns migration discovery, dependency ordering, and plan
construction.

## Planning

Migration files are discovered from configured roots and ordered by dependency,
then stable identifier. Planning rejects duplicate identifiers and dependency
cycles. Already-applied migrations are compared by checksum.

The `plan --dry-run` command performs validation and prints the exact ordered
steps without acquiring a lock, opening a write transaction, or executing SQL.
Dry runs may read local metadata and the target schema. A generated plan is not
a promise that later application will succeed.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Migration locking](migration-locking.md) | Provides neighboring architectural context |
| `related-to` | [Rollback policy](rollback-policy.md) | Provides neighboring architectural context |
| `related-to` | [Output rendering](output-rendering.md) | Provides neighboring architectural context |
| `related-to` | [Local cache](local-cache.md) | Provides neighboring architectural context |
