# Scenario: generated binding works without the initializer

## Initial project

The initializer has produced:

- a persistent project-instruction bootstrap;
- a compact `.specspine-integration.md` binding;
- an existing `<spine-root>/README.md` and linked specifications.

The binding records a concrete native workflow entry, downstream stage,
artifact paths, work-item naming rule, format source, context insertion point,
traceability rule, and conflict destination. `specspine-init` is unavailable to
the new agent.

## User request

```text
Prepare the native SDD change proposal for adding external authentication.
```

## Expected behavior

Using only persistent project instructions, the compact binding, native SDD
instructions, and SpecSpine, a fresh agent should:

- read the SpecSpine index and smallest relevant linked context;
- identify the native workflow entry without guessing;
- use a context insertion point only when one is defined;
- use work-item and artifact conventions only when present;
- place architectural context at the configured insertion point using the
  configured format source;
- preserve repository-root-relative path-plus-semantic-ID traceability when
  available;
- route conflicts to the configured destination when one was discovered,
  otherwise block and report them explicitly;
- avoid requiring `specspine-init`, a generated skill, or conversation history.

## Failure indicators

- the agent must rediscover basic framework conventions;
- a runtime binding is missing, vague, or unresolved;
- the agent reads all specifications instead of selecting relevant context;
- downstream artifacts silently override Decisions or Constraints;
- the initializer or another generated skill is required at runtime.
