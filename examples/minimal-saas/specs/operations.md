# Operations

Defines the runtime environment required to configure, deploy, and observe the
application.

## Responsibility

- provide environment-specific configuration;
- manage external credentials and secrets;
- expose service health;
- support deployment and incident diagnosis.

## Boundaries

Operations defines runtime mechanisms but does not own product behavior.

## Relationships

### Used by

- [Application](application.md)
- [Identity](identity.md)
- [Billing](billing.md)

## Decisions

- Secrets are supplied through the deployment environment.
- Health reporting distinguishes process availability from dependency health.

## Open questions

- Which deployment platform will host the first release?
- What observability is required before production launch?
