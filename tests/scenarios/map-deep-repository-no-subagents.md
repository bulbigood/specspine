# Scenario: large-repository mapping without subagents

## Existing SpecSpine

The large repository has a minimal architecture index. Several runtime,
data-flow, integration, deployment, and observability areas remain unmapped.
The execution environment cannot launch subagents.

## User request

```text
Use `$specspine-map-deep` to map the complete repository into SpecSpine.
```

## Expected behavior

The agent should:

- use the large-repository mapping protocol despite lacking subagents;
- discover the requested repository scope adaptively;
- create a disposable run root without persistent recovery state;
- act as one local producer, taking one architectural question at a time;
- inspect only evidence relevant to the current question;
- stage and publish each acceptable candidate with a filesystem
  move tool;
- continue from material follow-up questions in producer reports;
- avoid holding the whole repository map or all evidence in context;
- cover material cross-cutting flows before declaring saturation;
- stop each branch only when Map can add no useful architectural document;
- normalize once after saturation and report that execution was sequential
  because subagents were unavailable.

## Failure indicators

- the agent skips the large-repository protocol;
- the agent attempts one unbounded whole-repository source pass;
- the agent treats a few initial overview nodes as complete mapping;
- the agent creates a ledger, recovery manifest, or resumable run protocol;
- the agent manually reconstructs staged files during publication;
- normalization or Doctor runs before saturation.
