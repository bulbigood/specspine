# External identity

External identity authenticates humans through supported consumer identity providers without making provider tokens application sessions.

## Responsibility

It owns provider authorization initiation, callback validation, normalized external subject identity, and the handoff to account linking and session creation.

## Boundaries

- Matching an external subject to a user belongs to [account linking](account-linking.md).
- Application access belongs to [login sessions](login-sessions.md).
- Organization-managed federation belongs to [enterprise SSO](enterprise-sso.md).

## Interfaces

The public authorization endpoint binds provider, redirect destination, nonce, and PKCE state. The callback verifies that state and provider response, then produces a provider-independent identity assertion.

## Constraints

- Provider access or refresh tokens are never accepted as RelayHub bearer credentials.
- Callback state is single-use and bound to the initiating browser interaction.

## Open questions

- Which providers require retained delegated access distinct from login identity?


