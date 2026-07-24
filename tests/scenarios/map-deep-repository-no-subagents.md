# Scenario: complete repository mapping without subagents

## Existing SpecSpine

The controlled repository has only its runtime composition mapped. Six
independent responsibilities remain undocumented. The execution runtime does
not expose any subagent-creation capability.

## User request

```text
Use `$specspine-map` in exhaustive mode to document every useful architectural
branch of this repository until saturation.
```

## Expected behavior

The agent should:

- determine capability before reading the exhaustive orchestration reference;
- avoid reading `orchestration.md` because no subagent creator exists;
- read Map and its resources directly without building a producer bundle;
- discover the requested repository scope adaptively;
- keep pending architectural questions in memory;
- inspect only evidence relevant to the current question;
- write one coherent Map step directly to the live Spine;
- run the deterministic checker after each write and resolve errors early;
- continue through material follow-up and adjacent questions;
- avoid holding the whole repository map or all evidence in context;
- cover material cross-cutting flows before declaring saturation;
- stop each branch only when Map can add no useful architectural document;
- normalize once after saturation and recommend Doctor in a new session.

## Failure indicators

- the agent reads `orchestration.md` or builds producer instructions;
- any collaboration tool is invoked;
- the agent attempts one unbounded whole-repository source pass;
- the agent treats a few initial overview nodes as complete mapping;
- the agent creates staging, a run root, producer reports, or recovery state;
- a checker error is left unresolved while mapping continues;
- normalization or Doctor runs before saturation.
