# Scenario: connect an existing root and detect its language

## Initial project

A root `AGENTS.md` contains user-authored instructions. An existing
`architecture/README.md` and linked specification are written primarily in
Russian. No managed connection block exists.

## Stage 1: request connection

The user asks to connect SpecSpine without naming its root. The skill should ask
only for the root and make no changes.

## Stage 2: select existing root

The user selects `architecture`. The skill should inspect only that path, read
the root `README.md`, detect Russian as its clear dominant language, and offer
Russian as the documentation-language default. It should also offer
`AGENTS.md` as the remaining default. It must preserve every file.

## Stage 3: accept detected defaults

The user accepts the offered settings. The skill should add one managed block
to `AGENTS.md`, persist `architecture/README.md` and Russian, and leave
the existing SpecSpine byte-for-byte unchanged.

## Failure indicators

- `specspine` is inspected before the user selects a root;
- English is offered despite a clearly Russian root index;
- the existing index or linked specification is rewritten;
- another index or concept specification is created;
- user-authored project instructions are replaced.
