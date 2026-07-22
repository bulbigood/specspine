# Configuration and operations

Configuration and operations owns environment validation, dependency
coordinates, process lifecycle, logging level, and the supplied container and
process-manager topology.

## Responsibility

It turns environment variables into validated MongoDB, JWT, email, port, and
environment settings; establishes startup/shutdown behavior; and supplies
Docker Compose and PM2 deployment entry points.

## Boundaries

- Express composition belongs to the [API runtime](api-runtime.md).
- MongoDB data ownership belongs to [persistence](persistence.md).
- SMTP use belongs to [email delivery](email-delivery.md).
- Request log formatting and error responses belong to the
  [request pipeline](request-pipeline.md).

## Runtime topology

The supplied Compose topology contains one Node application service and one
MongoDB service on a private network with a persistent database volume. The
production overlay starts the application through PM2; its configuration runs
one autorestarted instance.

The intended topology adds independently scalable workers for
[background jobs](background-jobs.md) and [event delivery](event-delivery.md).
API and workers share durable state but expose separate readiness signals and
can be deployed without assuming in-process execution.

## Lifecycle

1. Environment configuration is loaded and validated during module import.
2. The executable connects to MongoDB.
3. After connection, the Express server listens on the configured port.
4. Uncaught exceptions and unhandled rejections trigger server close and an
   error exit; SIGTERM closes the HTTP server when present.

## Configuration

`NODE_ENV`, MongoDB URL, and JWT secret are required. Token lifetimes and port
have defaults. SMTP fields are optional at validation time even though email
delivery consumes them.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- The test environment appends `-test` to the configured MongoDB URL. Evidence:
  `src/config/config.js`, `tests/utils/setupTestDB.js`.
- Production process management declares one application instance. Evidence:
  `ecosystem.config.json`, `docker-compose.prod.yml`.
- Unexpected errors close the server and exit with status 1; SIGTERM closes
  without an explicit process exit in the handler. Evidence: `src/index.js`.
- Console logging is debug-level in development and info-level otherwise.
  Evidence: `src/config/logger.js`.

## Open questions

- No readiness/health endpoint or graceful MongoDB disconnect sequence is
  present, and the intended orchestration contract is not documented.
- Optional SMTP validation permits starting a deployment whose email flows
  cannot be configured successfully.

