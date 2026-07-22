# Persistence

Persistence is the MongoDB boundary for user and token state and the shared
Mongoose behaviors applied to those records.

## Responsibility

It owns connection-backed durable records, model validation and hooks,
reference relationships, safe JSON projection, and reusable paginated queries.

## Boundaries

- Capability-specific lifecycle rules belong to
  [user management](user-management.md) and
  [token lifecycle](token-lifecycle.md).
- Database connection startup and deployment belong to
  [configuration and operations](configuration-operations.md).

## Data model

- User records hold account profile, credentials, global role, and verification
  state.
- Token records refer to users and hold revocable refresh, password-reset, and
  email-verification credentials.
- Organization and membership records preserve tenant lifecycle and the
  unique user-organization relationship.
- Service-account and API-credential records preserve non-human identity while
  keeping raw credential secrets outside persistent storage.
- Job, event, webhook, idempotency, and audit records preserve retry identities
  and tenant ownership across API and worker processes.
- Mongoose timestamps exist on both models but the shared JSON transform omits
  them from API representations.

## Shared behavior

- The JSON plugin removes private paths and persistence metadata and maps `_id`
  to `id`.
- The pagination plugin combines filtered count and page retrieval, optional
  multi-field sorting, limits/pages, and optional nested population.
- Test setup connects to an environment-derived database suffixed with `-test`
  and clears all collections between tests.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- Services import Mongoose models directly; no repository or transaction
  abstraction is present. Evidence: `src/services/user.service.js`,
  `src/services/token.service.js`, `src/services/auth.service.js`.
- The token-to-user reference has no observed database-level cascade or TTL
  index. Evidence: `src/models/token.model.js`.
- Pagination performs count and retrieval concurrently and defaults to ten
  results on page one. Evidence: `src/models/plugins/paginate.plugin.js`,
  `tests/integration/user.test.js`.

## Inferred

- The direct model usage suggests this starter favors a thin service/data
  boundary over persistence portability; this is not recorded as accepted
  architectural intent.

## Relationships

- [API runtime](api-runtime.md)
- [Authentication](authentication.md)

