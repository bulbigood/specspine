# RelayHub architecture

## Purpose

RelayHub is a multi-tenant B2B SaaS platform for creating, running, and
operating integrations between external SaaS products and APIs. Human and
machine principals configure versioned connectors and workflows; durable
workers receive provider events, poll external systems, execute actions, and
retain auditable outcomes. Subscription plans govern product capability and
usage while tenant environments isolate development from production.

The current repository supplies an observed Node/Express/MongoDB starting
runtime. The RelayHub capability network records accepted intended architecture
without claiming that the starter implementation already conforms to it.

## Architecture map

### Platform foundation

- [API runtime](api-runtime.md) — composes the versioned HTTP application.
- [Request pipeline](request-pipeline.md) — protects input and normalizes HTTP failures.
- [Persistence](persistence.md) — provides durable MongoDB-backed state mechanics.
- [Background jobs](background-jobs.md) — executes recoverable asynchronous work.
- [Event delivery](event-delivery.md) — publishes durable internal domain notifications.
- [Configuration and operations](configuration-operations.md) — owns deployment and process lifecycle.
- [Service health](service-health.md) — exposes safe liveness and readiness signals.

### Identity and tenancy

- [Authentication](authentication.md) — coordinates human credential proof and recovery.
- [Login sessions](login-sessions.md) — owns revocable human access across devices.
- [External identity](external-identity.md) — proves identity through consumer providers.
- [Enterprise SSO](enterprise-sso.md) — connects organization-managed identity providers.
- [Organizations](organizations.md) — defines tenant identity and lifecycle.
- [Organization membership](organization-membership.md) — owns human tenant participation.
- [Service accounts](service-accounts.md) — owns tenant machine principals.
- [Access control](access-control.md) — evaluates human roles, memberships, and machine scopes.

### Integration platform

- [Connector catalog](connector-catalog.md) — describes supported external systems and capabilities.
- [Connections](connections.md) — owns tenant authorization to external accounts.
- [Credential vault](credential-vault.md) — protects recoverable provider secrets.
- [Connector triggers](connector-triggers.md) — normalizes external signals.
- [Connector actions](connector-actions.md) — defines outbound provider operations.
- [Inbound webhooks](inbound-webhooks.md) — verifies and accepts provider callbacks.
- [Polling triggers](polling-triggers.md) — collects changes from providers without push delivery.
- [External rate limits](external-rate-limits.md) — coordinates shared provider quotas.

### Workflow runtime

- [Workflow definitions](workflow-definitions.md) — owns editable workflows and immutable revisions.
- [Workflow triggers](workflow-triggers.md) — binds accepted start conditions.
- [Workflow executions](workflow-executions.md) — owns durable run lifecycle.
- [Step executions](step-executions.md) — performs and records connector action attempts.
- [Execution concurrency](execution-concurrency.md) — coordinates fair distributed capacity.
- [Execution retries](execution-retries.md) — classifies and schedules recoverable failures.
- [Dead-letter handling](dead-letter-handling.md) — preserves exhausted work for diagnosis.

### Product and operations

- [Tenant environments](tenant-environments.md) — isolates development, staging, and production state.
- [Plans and entitlements](plans-entitlements.md) — resolves commercial capabilities and limits.
- [Subscriptions](subscriptions.md) — owns renewable service periods and commercial status.
- [Usage metering](usage-metering.md) — records deduplicated billable consumption.
- [Payment processing](payment-processing.md) — reconciles provider collection outcomes.
- [Invoices](invoices.md) — owns finalized billed-period evidence.
- [Usage quotas](usage-quotas.md) — enforces tenant and platform safety limits.
- [Data retention](data-retention.md) — governs expiry, holds, and cleanup.
- [Audit log](audit-log.md) — preserves attributable security and administrative evidence.
- [Incident management](incident-management.md) — communicates platform disruption.
- [Support access](support-access.md) — governs exceptional tenant-approved assistance.

## System shape

RelayHub separates synchronous control-plane APIs from independently scalable
workers. API and workers share durable state, but external calls, polling,
webhook delivery, metering, and cleanup execute through recoverable jobs.
Every tenant runtime object carries explicit organization and environment
context. Connector releases and published workflow revisions are immutable so
historical executions remain interpretable.

The observed starter remains one Node.js HTTP process backed by MongoDB and an
optional SMTP server. It has no observed queue, worker, server-side session
store, connector runtime, billing provider integration, or environment model.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- The repository exposes one versioned REST API process and stores application
  state in MongoDB. Evidence: `src/index.js`, `src/app.js`, `docker-compose.yml`.
- Authentication, users, and development-only API documentation are the
  observed public route groups. Evidence: `src/routes/v1/index.js`.

## Open questions

- Which initial connector providers define the first production catalog?
- Which payment provider, supported currencies, and tax boundary are required?
- Which workflow expression language and sandbox satisfy mapping needs?
- Which enterprise SSO protocols and MFA factors are required initially?
- Which regions, availability targets, and data-residency guarantees apply?

