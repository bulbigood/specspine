# Scenario: documenting code routes to Map

## User request

```text
Document the observed architecture of the order-cancellation code in the
project architecture documentation. Derive it from `src/orders/cancel.js`;
record observed behavior without inventing intended decisions. Do not change
the implementation.
```

## Expected behavior

The agent should reject Extract as the active workflow and load
`specspine-map`, because the task maps observed brownfield code into SpecSpine.
It must not invoke `search_spine.py`, must preserve the implementation, and
must modify only SpecSpine documentation.
