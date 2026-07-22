# Connector actions

Connector actions define versioned outbound operations that workflow steps can invoke on external systems.

## Responsibility

They own action identity, input and output schema references, connection requirements, idempotency capability, timeout class, and normalized failure categories.

## Boundaries

- Release immutability belongs to [connector versions](connector-versions.md).
- Data conversion belongs to [data mappings](data-mappings.md).
- Attempts and retries belong to [step executions](step-executions.md).
- Provider quota coordination belongs to [external rate limits](external-rate-limits.md).

## Interfaces

The runtime invokes an action with an exact version, tenant connection, validated input, execution identity, and deadline. It returns schema-valid output or a classified retryable, authorization, throttling, input, or terminal provider failure.

## Constraints

- Provider-specific error payloads are sanitized before entering durable execution history.
- Retryable actions preserve a stable idempotency identity when the provider supports one.


