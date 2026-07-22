# External API credentials

External API credentials authorize tenant connections to providers that use API keys, tokens, or client certificates instead of OAuth.

## Responsibility

This capability owns credential-field requirements, one-time submission, validation handoff, rotation, and removal from a connection.

## Boundaries

- Encrypted storage and decryption authority belong to the [credential vault](credential-vault.md).
- Connection health belongs to [connections](connections.md).
- RelayHub client secrets belong to [API credentials](api-credentials.md).

## Behavior

Administrators submit required secret fields over an authenticated tenant boundary. Values are written directly to the vault and replaced by safe references. Rotation validates the replacement before retiring prior material when the provider permits overlap.

## Constraints

- Raw external credentials are never returned by read, audit, or execution-history interfaces.
- Validation failures must not expose provider secrets or full provider responses.


