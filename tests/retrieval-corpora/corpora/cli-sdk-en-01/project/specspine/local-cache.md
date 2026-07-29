# Local cache

**ID:** `local-cache` · **Kind:** `concept`

**Summary:** Owns the durable architectural concept `local-cache`.

## Responsibility

The cache stores non-secret registry metadata and migration checksums for
offline inspection.

## Behavior

Entries have a namespace, schema version, and expiry. A read may use stale
metadata only when the caller explicitly requests offline mode. Writes use
atomic replacement. Corrupt entries are discarded and fetched again.

The cache accelerates discovery and planning but does not authorize a
migration, prove lease ownership, or store credentials. Clearing cached data
cannot alter the applied migration ledger.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Migration planning](migration-planning.md) | Provides neighboring architectural context |
| `related-to` | [Credential store](credential-store.md) | Provides neighboring architectural context |
| `related-to` | [Plugin API](plugin-api.md) | Provides neighboring architectural context |
