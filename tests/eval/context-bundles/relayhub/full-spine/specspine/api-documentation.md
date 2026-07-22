# API documentation

API documentation assembles the service's OpenAPI description and exposes an
interactive Swagger UI as a development-only route.

## Responsibility

It owns API metadata, shared schemas and responses, discovery of route-level
operation annotations, and the HTTP adapter that serves the resulting contract.

## Boundaries

- Route execution and environment-dependent mounting belong to the
  [API runtime](api-runtime.md).
- Endpoint behavior belongs to [authentication](authentication.md) and
  [user management](user-management.md), and the intended tenant capabilities;
  documentation describes interfaces but does not own their behavior.
- Runtime environment and port values belong to
  [configuration and operations](configuration-operations.md).

## Behavior

- OpenAPI 3 metadata combines package version and configured local server port
  with reusable component definitions and annotations colocated with v1 routes.
- Swagger UI is mounted at `/v1/docs` only when the application starts in the
  development environment; the route is absent in production and test.
- The UI enables contract exploration and serves the assembled in-memory
  specification rather than a committed generated artifact.
- The intended contract groups operations by stable capability and distinguishes
  tenant control-plane APIs from provider-facing callback interfaces.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- Contract discovery reads YAML definitions under `src/docs` and JSDoc
  annotations under `src/routes/v1`. Evidence: `src/routes/v1/docs.route.js`,
  `src/docs/components.yml`, `src/routes/v1/auth.route.js`,
  `src/routes/v1/user.route.js`.
- The documentation route is conditionally mounted only in development.
  Evidence: `src/routes/v1/index.js`, `tests/integration/docs.test.js`.
- The advertised server URL is local HTTP at the configured application port.
  Evidence: `src/docs/swaggerDef.js`.

## Open questions

- The repository does not establish whether the assembled OpenAPI contract is
  published or validated outside the development UI.

## Relationships

- [Request pipeline](request-pipeline.md)

