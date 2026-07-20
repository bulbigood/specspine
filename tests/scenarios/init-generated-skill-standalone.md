# Scenario: generated integration works without the initializer

## Initial project

The initializer has produced:

- a persistent project-instruction bootstrap;
- a project-local integration skill and supported metadata;
- an existing `<spine-root>/README.md` and linked specifications.

The generated skill records a concrete native workflow entry, downstream
stage, artifact paths, work-item naming rule, format source, context insertion
point, traceability rule, and conflict destination. `specspine-init` is
unavailable to the new agent.

## User request

```text
Prepare the native SDD change proposal for adding external authentication.
```

## Expected behavior

Using only persistent project instructions, the generated skill, and
SpecSpine, a fresh agent should:

- discover and invoke the generated integration skill;
- read the SpecSpine index and smallest relevant linked context;
- identify the exact native workflow entry, work-item identifier, and artifact
  destination without inventing a naming convention;
- place architectural context at the configured insertion point using the
  configured format source;
- preserve path-plus-semantic-ID traceability when available;
- route conflicts and blocking questions to the configured destination;
- avoid requiring `specspine-init` or conversation history.

## Failure indicators

- the agent must rediscover basic framework conventions;
- a runtime binding is missing, vague, or unresolved;
- the agent reads all specifications instead of selecting relevant context;
- downstream artifacts silently override Decisions or Constraints;
- the initializer is required at runtime.
