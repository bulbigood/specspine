# Scenario: code fix does not invoke Extract

## User request

```text
Fix `cancelOrder` so it rejects an already cancelled order instead of silently
accepting it. Make the smallest code change in the named implementation file.
Do not consult or update project documentation.
```

## Expected behavior

The agent should edit the named source file directly. Loading the installed
Extract instructions must not cause `search_spine.py` to run because the
operator explicitly excluded project-documentation retrieval.
