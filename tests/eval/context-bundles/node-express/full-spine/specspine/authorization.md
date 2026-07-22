# Authorization

Owns the canonical role vocabulary, rights assigned to each role, and enforcement of required rights.

## Decisions

- Role names and their rights have one executable source of truth.
- Validation and documentation consume or reflect the canonical role vocabulary rather than defining competing authorization policy.
- The `auditor` role may list and view users through `getUsers`, but never receives `manageUsers`.

## Open questions

- A bootstrap administrator policy is unresolved. The system has not decided how the first eligible account is identified, how concurrent registrations are serialized, or whether deployment configuration must explicitly enable bootstrap. Registration must not silently choose this security policy.

## Relationships

- [Users](users.md)
- [API delivery](api.md)
