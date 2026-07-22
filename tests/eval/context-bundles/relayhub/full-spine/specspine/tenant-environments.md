# Tenant environments

Tenant environments isolate development, staging, and production integration configuration inside one organization.

## Responsibility

They own environment identity, class, lifecycle, environment-scoped connections, workflows, credentials, executions, and access policy.

## Boundaries

- Tenant identity belongs to [organizations](organizations.md).
- Definition movement belongs to [environment promotion](environment-promotion.md).
- Secret custody belongs to [credential vault](credential-vault.md).

## Behavior

Every workflow, connection, execution, trigger, and secret reference carries an explicit environment. Production environments can require stricter permissions and approval without sharing runtime objects with non-production environments.

## Constraints

- Credentials and live execution state never move between environments.
- Environment context is explicit at every tenant runtime boundary and cannot be inferred from a user's last selection.


