# Account linking

Account linking maintains the trusted relationship between one RelayHub user and one or more authentication identities.

## Responsibility

It owns identity-link uniqueness, explicit linking and unlinking, collision handling, and the guarantee that an account retains a usable authentication method.

## Boundaries

- Provider proof belongs to [external identity](external-identity.md) or [enterprise SSO](enterprise-sso.md).
- User profile ownership belongs to [user management](user-management.md).
- Session issuance belongs to [login sessions](login-sessions.md).

## Behavior

An authenticated user may link a newly proven identity. An external subject can belong to at most one user. Matching email alone does not silently transfer ownership between accounts. Unlinking is rejected when it would leave no permitted login method.

## Open questions

- May verified-email matches offer a separately confirmed merge flow?
- Can an enterprise administrator force removal of an organization-managed identity link?


