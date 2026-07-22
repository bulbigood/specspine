# Email delivery

Email delivery adapts authentication notifications to an external SMTP server.

## Responsibility

It owns SMTP transport construction and the textual password-reset and
email-verification messages sent on behalf of authentication flows.

## Boundaries

- Token creation and consumption belong to the
  [token lifecycle](token-lifecycle.md).
- Deciding when to send notifications belongs to
  [authentication](authentication.md).
- SMTP credentials and sender identity belong to
  [configuration and operations](configuration-operations.md).

## Interfaces

The adapter accepts recipient, subject, and text for generic delivery. The two
purpose-specific helpers embed a supplied token in a frontend URL and delegate
to that transport.

## Failure behavior

SMTP send failures propagate into the calling HTTP operation. Outside tests,
startup verifies the SMTP transport asynchronously and logs success or a
warning, but a failed verification does not terminate the API process.

<!-- specspine:evidence-baseline source=commit-179ae84; inspected=2026-07-22 -->
## Observed

- Email is sent synchronously within forgot-password and send-verification HTTP
  requests; there is no queue or retry worker. Evidence:
  `src/controllers/auth.controller.js`, `src/services/email.service.js`.
- Purpose-specific links use hard-coded placeholder frontend hosts. Evidence:
  `src/services/email.service.js`.

## Open questions

- Delivery retry, timeout, and user-facing failure policy are not defined.
- Frontend base URLs are not part of validated runtime configuration.

