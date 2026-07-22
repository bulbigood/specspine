# Scenario: initialize a generic project-agent integration

## Initial project

`specspine/README.md` exists and links to several architectural
specifications. A root `AGENTS.md` contains user-authored instructions but no
SpecSpine notice.

## User request

```text
Connect this SpecSpine to my coding agent. Use English for all SpecSpine
documentation. Apply the integration immediately.
```

## Expected behavior

The skill should:

- resolve `specspine` as `<spine-root>` and verify its index;
- inspect only the index and applicable persistent agent instructions;
- add one balanced managed bootstrap to `AGENTS.md` without changing other
  content;
- persist English as the SpecSpine documentation language in that bootstrap;
- create no additional artifact or project-local skill;
- point the bootstrap to `specspine/README.md`;
- distinguish Decisions and Constraints from Observed, Inferred, and Open
  questions;
- avoid modifying SpecSpine documents, source code, or unrelated files;
- produce exactly one managed block.

## Failure indicators

- the entire `AGENTS.md` is replaced;
- a project-local skill or additional integration artifact is generated;
- detailed workflow prose is placed in the always-loaded bootstrap;
- a template placeholder remains;
- implementation files are inspected or modified;
- global configuration is modified.
