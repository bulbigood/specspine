# Scenario: large-repository mapping without subagents

## Existing SpecSpine

The large repository has a minimal architecture index. Several runtime,
data-flow, integration, deployment, and observability areas remain unmapped.
The execution environment cannot launch subagents.

## User request

```text
Use `$specspine-map-large` to map the complete repository into SpecSpine.
```

## Expected behavior

The agent should:

- use the large-repository mapping protocol despite lacking subagents;
- create a disposable run root with a minimal recovery ledger;
- perform only a shallow topology scan and seed a bounded ready queue;
- act as one local producer, taking one architectural question at a time;
- inspect only evidence relevant to the current question;
- stage, read once, and publish each acceptable candidate with a filesystem
  move tool;
- checkpoint after publication and continue from producer reports;
- avoid holding the whole repository map or all evidence in context;
- cover material cross-cutting flows before declaring saturation;
- normalize once after saturation and report that execution was sequential
  because subagents were unavailable.

## Failure indicators

- the agent skips the large-repository protocol;
- the agent attempts one unbounded whole-repository source pass;
- the agent treats a few initial overview nodes as complete mapping;
- queue state exists only in conversational context;
- the agent manually reconstructs staged files during publication;
- normalization or Doctor runs before saturation.
