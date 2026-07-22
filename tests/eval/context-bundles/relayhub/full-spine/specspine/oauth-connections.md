# OAuth connections

OAuth connections acquire and renew delegated provider authorization for tenant connector connections.

## Responsibility

They own authorization state, callback correlation, granted scopes, token refresh, provider revocation, and reauthorization signaling.

## Boundaries

- Connection identity and health belong to [connections](connections.md).
- Encrypted token custody belongs to the [credential vault](credential-vault.md).
- Human login through an identity provider belongs to [external identity](external-identity.md).

## Behavior

Authorization initiation binds tenant, connector, requested scopes, redirect target, PKCE verifier, and single-use state. Callback success stores delegated credentials and activates the connection. Invalid grants or revoked refresh credentials move it to authorization-required without deleting workflow references.

## Constraints

- OAuth state is single-use and expires before authorization can be replayed.
- Requested scopes are the minimum required by selected connector capabilities.

## Open questions

- Who may approve scope expansion for an existing connection?


