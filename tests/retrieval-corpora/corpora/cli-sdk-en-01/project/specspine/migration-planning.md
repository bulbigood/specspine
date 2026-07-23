# Migration planning

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

- [Migration locking](migration-locking.md)
- [Rollback policy](rollback-policy.md)
- [Output rendering](output-rendering.md)
- [Local cache](local-cache.md)
