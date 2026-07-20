# Identity

Authenticates users and establishes the organization context used by the
application.

## Responsibility

- authenticate a user;
- create an application session;
- associate the user with an organization;
- expose the authenticated identity and tenant context.

## Boundaries

Identity does not decide subscription access. That policy belongs to
[Billing](billing.md) and the consuming workflow in
[Application](application.md).

## Relationships

### Used by

- [Application](application.md)

### Related

- [Operations](operations.md)

## Decisions

- Application sessions do not depend on the authentication provider.
- Organization identity is explicit in the authenticated context.

## Open questions

- Can one session switch between multiple organizations?
- Which authentication methods are required for the first release?
