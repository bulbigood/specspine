# Scenario: initialize and connect an unconfigured project

## Initial project

A root `AGENTS.md` contains user-authored instructions. No SpecSpine directory
or managed connection block exists.

## Stage 1: request connection

The user asks to connect SpecSpine without supplying configuration.

The skill should ask only for the SpecSpine root, defaulting to `specspine`.
It must not inspect that path or ask for a language before the operator selects
the root. The first stage must not change project files.

## Stage 2: select the root

The user selects the default `specspine` root. The path does not exist.

The skill should inspect that exact path, then ask for the remaining choices:

- documentation language, defaulting to English;
- project instruction file, defaulting to `AGENTS.md`.

The second stage must not change project files.

## Stage 3: accept remaining defaults

The user accepts all offered defaults and asks the skill to complete the
connection.

The skill should:

- preserve the user-authored `AGENTS.md` content;
- add exactly one managed connection block to `AGENTS.md`;
- persist the `specspine` directory and English in the block;
- create English `specspine/README.md` plus deterministic
  `specspine/_INDEX.md` and `specspine.json`;
- create no concept specifications or other artifacts.

## Failure indicators

- configuration defaults are applied before the user answers;
- the language is requested before the root is selected and inspected;
- the skill refuses because the `specspine` directory is absent;
- existing project instructions are replaced;
- the root README or index contains unresolved template placeholders;
- files other than `AGENTS.md`, `specspine/README.md`,
  `specspine/_INDEX.md`, and `specspine.json` are created or changed.
