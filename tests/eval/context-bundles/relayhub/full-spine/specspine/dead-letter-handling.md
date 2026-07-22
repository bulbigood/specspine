# Dead-letter handling

Dead-letter handling preserves exhausted or administratively blocked execution work for diagnosis and controlled recovery.

## Responsibility

It owns dead-letter identity, reason, safe failure evidence, retention, acknowledgement, and replay authorization.

## Boundaries

- Retry exhaustion belongs to [execution retries](execution-retries.md).
- New recovery runs belong to [execution replay](execution-replay.md).
- Security and administrative evidence belongs to [audit log](audit-log.md).

## Interfaces

Authorized tenant operators can list and inspect dead letters, acknowledge them, or request replay after correcting configuration. A dead letter links to its workflow revision, execution, step, connection, and final attempt without containing credentials.

## Constraints

- Dead letters are not executable queue items and cannot be silently redelivered.
- Replay creates linked new state; it never rewrites the failed historical execution.


