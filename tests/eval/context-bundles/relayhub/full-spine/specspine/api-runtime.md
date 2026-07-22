# API runtime

The API runtime is the composition boundary for the single Express HTTP
application and its versioned route surface.

## Responsibility

It assembles global middleware, Passport JWT support, `/v1` routes, the
not-found boundary, and final error handling. The executable entry point first
connects to MongoDB and only then begins listening for HTTP requests.

## Boundaries

- Transport-wide middleware and failure translation belong to the
  [request pipeline](request-pipeline.md).
- Identity flows belong to [authentication](authentication.md); user CRUD
  belongs to [user management](user-management.md).
- OpenAPI contract assembly and development-only Swagger UI exposure belong to
  [API documentation](api-documentation.md).
- Process startup and termination belong to
  [configuration and operations](configuration-operations.md).

## Interfaces

- The observed `/v1/auth` and `/v1/users` groups expose starter identity and
  user operations.
- The intended control plane adds organization-scoped groups for memberships,
  service accounts, connectors, connections, workflows, executions, webhooks,
  audit, environments, and billing. Their capability specifications own the
  contracts; this runtime owns only composition and versioning.
- Provider-addressable callbacks are isolated under the
  [inbound webhook](inbound-webhooks.md) boundary rather than tenant control
  plane authorization.
- Unknown API requests enter the common 404/error response path.

## Behavior

Middleware order establishes the request boundary before routes run: logging,
security headers, body parsing, sanitization, compression, CORS, Passport, an
optional production authentication rate limiter, routes, 404 conversion, and
error handling.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- MongoDB connection success gates server startup. Evidence: `src/index.js`.
- All route handlers execute inside one Express application and process.
  Evidence: `src/app.js`, `src/routes/v1/index.js`.

## Relationships

- [Persistence](persistence.md)
- [Access control](access-control.md)
- [API documentation](api-documentation.md)
- [Configuration and operations](configuration-operations.md)

