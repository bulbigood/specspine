# Architecture context handoff

## Change intent

Evaluate automatic bootstrap-administrator creation without silently selecting a security policy.

## Primary specification

`specspine/authorization.md`

## Required specifications

- `specspine/users.md`

## Blocking questions

- How is the first eligible account identified?
- How are concurrent registrations serialized?
- Must deployment configuration explicitly enable bootstrap?

## Expected architectural outcome

Registration remains unchanged until the bootstrap policy is accepted.
