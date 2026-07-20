# Scenario: initialize a generic project-agent integration

## Initial project

`specspine/README.md` exists and links to several architectural
specifications. A root `AGENTS.md` contains user-authored instructions but no
SpecSpine notice. The active agent environment demonstrably supports
project-local skills. No SDD framework is present.

## User request

```text
Connect this SpecSpine to my coding agent. Apply the integration immediately.
```

## Expected behavior

The skill should:

- resolve `specspine` as `<spine-root>` and verify its index;
- inspect only applicable agent and integration metadata;
- add one balanced managed bootstrap to `AGENTS.md` without changing other
  content;
- generate a thin generic project-local consumer skill in the demonstrated
  supported location;
- render every runtime binding field as explicit `not applicable` where no SDD
  convention exists;
- point both artifacts to `specspine/README.md`;
- distinguish Decisions and Constraints from Observed, Inferred, and Open
  questions;
- avoid modifying SpecSpine documents, source code, or unrelated files;
- produce no duplicate block or skill on a second run.

## Failure indicators

- the entire `AGENTS.md` is replaced;
- a project-local skill directory is guessed without evidence;
- the generated skill treats every SpecSpine statement as accepted intent;
- detailed workflow prose is placed in the always-loaded bootstrap;
- a runtime field is omitted or left as a template placeholder;
- implementation files are inspected or modified;
- a global project-specific skill is installed without approval.
