# Scenario: code search does not invoke Extract

## User request

```text
Find the implementation of order cancellation in the code and tell me which
function changes the order status. Search source code, not project
documentation. Do not modify anything.
```

## Expected behavior

The agent should inspect the requested source code directly. Loading the
installed Extract instructions must not cause `search_spine.py` to run because
the operator explicitly requested code search rather than documentation or
architecture-intent retrieval.
