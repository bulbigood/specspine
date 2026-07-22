# Support access

Support access provides exceptional, time-bounded platform assistance inside an organization without granting ambient administrator authority.

## Responsibility

It owns support request identity, tenant approval, purpose, scope, duration, operator attribution, revocation, and evidence of every privileged action.

## Boundaries

- Ordinary tenant authorization belongs to [access control](access-control.md).
- Organization approval belongs to [organization membership](organization-membership.md).
- Evidence belongs to [audit log](audit-log.md).
- Incident context belongs to [incident management](incident-management.md).

## Behavior

An authorized tenant principal grants a named support scope for a bounded period. The support operator explicitly enters that context; requests carry both operator and tenant approval identities. Expiry or revocation immediately denies further action.

## Constraints

- Support access cannot reveal raw credentials, payment instruments, or authentication factors.
- No standing platform role implicitly grants tenant data access.


