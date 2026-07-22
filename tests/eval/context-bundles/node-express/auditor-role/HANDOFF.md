# Architecture context handoff

## Change intent

Add a read-only auditor role without changing existing authorization boundaries.

## Primary specification

`specspine/authorization.md`

## Required specifications

- `specspine/users.md`

## Architectural decisions and constraints

- Role names and rights have one executable source of truth.
- Validation and public documentation reflect that canonical vocabulary.
- Auditors receive `getUsers` and never `manageUsers`.

## Expected architectural outcome

Auditors can list and view users; user and admin behavior is unchanged.
