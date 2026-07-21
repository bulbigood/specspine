# SpecSpine package generation contract

## Source and output

Canonical sources live under:

```text
assets/skill-sources/
├── specspine-init/
├── specspine-grow/
├── specspine-map/
└── specspine-doctor/
```

Canonical entrypoints are named `SKILL.md.src` so skill installers do not
discover source templates as additional runtime skills. Generation renames each
one to `SKILL.md` in its output package.

The generator copies them to sibling publishable skill directories and writes
`.generated-by-specspine-adapter-generator.json` with source hashes. Generated
directories must not contain additional files except ignored local artifacts.

## Shared rules

The `specspine-grow` source owns the canonical copies of:

- `references/spec-format.md`;
- `references/spec-semantics.md`;
- `references/context-handoff.md`.

Copy those files at build time into every runtime skill that needs them. Test
byte equality. Do not replace them with runtime cross-skill reads: independently
installed skills cannot reliably locate each other's resources, and version
skew would make claim classification unsafe.

## Project adaptation boundary

Package generation resolves framework-maintainer duplication. It cannot know a
consumer project's agent instructions, SpecSpine root, SDD workflow, paths, or
naming rules.

`specspine-init` may therefore generate only:

- one small persistent discovery block;
- one compact project binding when a downstream SDD workflow exists.

It must not generate another project-local skill. Generic integrations need
only the discovery block.

## Required gates

Before publishing:

1. regenerate all packages;
2. run generation in `--check` mode;
3. validate every generated skill with an available native validator;
4. run unit tests and the eval-manifest audit;
5. run deterministic scripts on representative valid and invalid fixtures;
6. inspect the generated diff for unintended prompt growth;
7. record the release version through the repository's release mechanism.

Generation and testing do not authorize external publishing.

The generator enforces maximum word counts for the always-loaded bootstrap,
conditional project binding, and latency-sensitive `init` and `doctor` skill
bodies. Change a budget only with an explicit architectural reason and a before
and after runtime-cost comparison.
