# Inbound webhooks

Inbound webhooks receive provider callbacks and connector events at public, provider-addressable endpoints.

## Responsibility

They own endpoint routing, raw-body preservation, provider signature verification, replay-window checks, acknowledgement, and durable handoff to trigger or payment processing.

## Boundaries

- Event normalization belongs to [connector triggers](connector-triggers.md).
- Financial callback interpretation belongs to [payment processing](payment-processing.md).
- Internal publication belongs to [event delivery](event-delivery.md).

## Behavior

Endpoints resolve a provider and tenant-safe binding without exposing credentials. Authentic callbacks are durably accepted before success is acknowledged. Duplicate delivery retains provider event identity for downstream idempotency; unauthenticated payloads produce no domain effects.

## Constraints

- Signature verification uses the exact received bytes and bounded timestamp or nonce policy.
- Public endpoints do not disclose whether a guessed tenant, connection, or subscription exists.


