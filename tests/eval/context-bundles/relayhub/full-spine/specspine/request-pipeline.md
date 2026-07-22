# Request pipeline

The request pipeline protects and normalizes HTTP input before capability
handlers run, and converts failures into a common external response.

## Responsibility

It owns cross-cutting HTTP concerns: security headers, JSON and form parsing,
input sanitization, CORS, compression, request validation, async error
forwarding, status conversion, and request/error logging.

## Boundaries

- Route selection and composition belong to the [API runtime](api-runtime.md).
- Bearer identity and permission checks belong to
  [access control](access-control.md).
- Capability services decide domain failures; this pipeline only carries and
  serializes them.

## Behavior

- Route-specific Joi schemas select and validate request params, query, and
  body, then replace them with normalized values.
- Async controllers forward rejected work to Express error middleware.
- Non-application errors are converted to a common API error. In production,
  non-operational failures are masked as internal-server errors; development
  responses can include stacks.
- Successful and failed requests use separate Morgan-to-Winston streams outside
  tests.
- Production limits repeated failed authentication requests before auth routes
  execute.

## Failure behavior

The external error contract is `{ code, message }`, with an optional stack in
development. Unknown routes become 404 errors. Authentication and validation
failures enter this same response boundary.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- Validation rejects all discovered field errors together and only considers
  params, query, and body declared by the route schema. Evidence:
  `src/middlewares/validate.js`.
- Production masks non-operational errors while retaining operational status
  and message. Evidence: `src/middlewares/error.js`,
  `tests/unit/middlewares/error.test.js`.
- The auth limiter counts failed requests and is installed only in production.
  Evidence: `src/app.js`, `src/middlewares/rateLimiter.js`.

## Relationships

- [Authentication](authentication.md)
- [User management](user-management.md)

