# Credential vault

The credential vault is the security boundary for recoverable secrets needed to call external systems.

## Responsibility

It owns encrypted secret versions, key references, scoped retrieval, rotation, deletion scheduling, and access evidence.

## Boundaries

- Secret meaning and required fields belong to [OAuth connections](oauth-connections.md) and [external API credentials](external-api-credentials.md).
- Caller authorization belongs to [access control](access-control.md).
- Security-event history belongs to [audit log](audit-log.md).

## Interfaces

Write returns an opaque secret reference. Runtime retrieval requires tenant, connection, operation, and execution context. Administrative APIs can rotate or revoke references but cannot read plaintext.

## Constraints

- Plaintext exists only for the bounded write or provider-call operation and is excluded from logs, events, errors, and job payloads.
- A secret reference cannot be resolved outside its owning organization and connection.

## Open questions

- Which managed key service and recovery boundary are required per deployment tier?


