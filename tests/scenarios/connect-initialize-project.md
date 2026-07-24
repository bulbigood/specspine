# Scenario: initialize and connect an unconfigured project

## Initial project

A root `AGENTS.md` contains user-authored instructions. No SpecSpine directory
or managed connection block exists.

## Stage 1: request setup

The user asks to set up SpecSpine without supplying configuration.

The skill should ask only for the SpecSpine root, defaulting to `specspine`.
It must not inspect that path or ask for a language before the operator selects
the root. The first stage must not change project files.

## Stage 2: select the root

The user selects the default `specspine` root. The path does not exist.

The skill should inspect that exact path, then ask for the remaining choices:

- documentation language, defaulting to English;
- project instruction file, defaulting to `AGENTS.md`;
- retrieval accelerator, defaulting to `auto`.

The second stage must not change project files.

## Stage 3: accept remaining defaults

The user accepts all offered defaults and asks the skill to complete setup.

The skill should:

- preserve the user-authored `AGENTS.md` content;
- add exactly one managed connection block to `AGENTS.md`;
- persist `specspine/README.md`, English, and `auto` in the block;
- create a minimal English `specspine/README.md`;
- create no concept specifications or other artifacts.

## Failure indicators

- configuration defaults are applied before the user answers;
- the language is requested before the root is selected and inspected;
- the skill refuses because `specspine/README.md` is absent;
- existing project instructions are replaced;
- the root index contains unresolved template placeholders;
- files other than `AGENTS.md` and `specspine/README.md` are created or changed.
