# Authorization

Owns the canonical role vocabulary, rights assigned to each role, and enforcement of required rights.

## Decisions

- Role names and rights have one executable source of truth.
- Validation and public documentation consume or reflect that vocabulary rather than defining competing policy.
- The `auditor` role receives `getUsers` but never `manageUsers`.
