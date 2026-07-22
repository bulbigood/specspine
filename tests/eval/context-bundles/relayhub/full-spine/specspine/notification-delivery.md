# Notification delivery

Notification delivery sends product and operational messages to organization members through configured channels.

## Responsibility

It owns notification type, recipient resolution, preference and severity policy, template version, channel attempts, deduplication, and delivery history.

## Boundaries

- Authentication-specific SMTP adaptation remains with [email delivery](email-delivery.md).
- Source incidents and execution failures remain owned by their capabilities.
- Durable dispatch uses [background jobs](background-jobs.md).

## Interfaces

Capabilities publish a typed notification request with tenant, recipients or role, severity, safe variables, and stable source identity. Users manage non-mandatory preferences; security and billing-critical messages may be non-optional.

## Constraints

- Notification content excludes credentials and unredacted provider payloads.
- Channel retries do not produce duplicate user-visible messages for one source identity where the channel supports deduplication.


