# Enterprise SSO

Enterprise SSO lets an organization authenticate members through its managed identity provider and domain policy.

## Responsibility

It owns SSO connection configuration, verified domains, provider metadata rotation, tenant discovery, assertion validation, and enforcement policy.

## Boundaries

- Global user identity belongs to [user management](user-management.md).
- Linking the asserted subject belongs to [account linking](account-linking.md).
- Tenant participation belongs to [organization membership](organization-membership.md).

## Interfaces

Organization administrators configure and activate an SSO connection after domain and metadata verification. Login discovery selects an active connection without granting tenant membership. Valid assertions produce a normalized identity proof for linking and session creation.

## Constraints

- An SSO assertion never bypasses active organization membership.
- Configuration and certificate changes are auditable and preserve a recoverable prior version during rotation.

## Open questions

- Is just-in-time membership provisioning allowed, and under which default role?


