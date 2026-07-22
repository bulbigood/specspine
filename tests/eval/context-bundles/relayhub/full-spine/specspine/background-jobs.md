# Background jobs

Background jobs execute durable asynchronous work that must survive API
process restarts and must not extend request latency.

## Responsibility

This capability owns job persistence, availability time, leasing, attempt
tracking, retry scheduling, terminal failure, cancellation, and worker
execution identity.

## Boundaries

- Calling capabilities own business retry eligibility and job payload meaning.
- [Event delivery](event-delivery.md) owns event publication and consumer
  progress, not generic work scheduling.
- [Idempotency](idempotency.md) protects business effects when a job may execute
  more than once.
- Process deployment and worker health belong to
  [configuration and operations](configuration-operations.md).

## Interfaces

Capability services enqueue a typed job with tenant, payload reference,
availability time, and stable operation identity. Workers claim available jobs
under a time-limited lease and report success, retryable failure, terminal
failure, or cancellation.

- `GET /v1/organizations/{organizationId}/jobs/{jobId}` exposes safe status for
  tenant-visible operations.
- `POST /v1/organizations/{organizationId}/jobs/{jobId}/cancel` requests
  cancellation when the owning capability declares it safe.

## Delivery behavior

Execution is at least once. Lease expiry makes interrupted work available
again; workers therefore cannot assume a single invocation. Exponential delay
and attempt ceilings are policy inputs supplied by the job type.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-job-at-least-once** — Job handlers must tolerate repeated execution of
  the same stable job identity.
- **CON-job-tenant-context** — Every tenant-owned job retains immutable
  organization context through retries.
<!-- specspine:semantic-ids:end -->

## Open questions

- Which job categories require ordered execution?
- Who may replay terminal failures, and how is replay audited?

## Relationships

- [Persistence](persistence.md)
- [Audit log](audit-log.md)

