# Scenario: reconnect an already integrated generic agent

## Initial project

`specspine/README.md` exists and links to an architectural specification. The
root `AGENTS.md` contains user-authored instructions and one complete SpecSpine
managed bootstrap.

## User request

```text
Connect this SpecSpine to my coding agent. Keep English as the language for all
SpecSpine documentation and keep its retrieval accelerator disabled. Apply the
integration immediately.
```

## Expected behavior

The skill should:

- recognize the existing managed bootstrap;
- leave exactly one balanced managed block in `AGENTS.md`;
- preserve the user-authored content and existing effective integration;
- preserve the extract-first retrieval route and Markdown fallback;
- preserve the `disabled` retrieval-accelerator policy;
- create no additional artifact or project-local skill;
- avoid changing SpecSpine documents, source code, or unrelated files;
- make no file changes when the integration is already current.

## Failure indicators

- a second managed block is appended;
- the existing bootstrap or user content is damaged;
- an additional integration artifact or project-local skill is generated;
- any project file is changed despite the integration already being current.
