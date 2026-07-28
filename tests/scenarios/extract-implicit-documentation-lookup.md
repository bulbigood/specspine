# Scenario: implicit project-documentation lookup

## User request

```text
Find what the project architecture documentation says about cancelling an
order. Include the transactional cancellation rule. Do not modify anything.
```

## Expected behavior

The agent should use `specspine-extract` because the connected project
instructions establish SpecSpine as the primary architecture-intent
documentation, even though the request names neither SpecSpine nor the skill.
It should answer from the smallest relevant source set and preserve the source
path, evidence status, constraints, and open questions.
