# SpecSpine resource generation contract

## Canonical packages

The publishable packages under `<repo-root>/skills/specspine-*` are the only
canonical skill sources. Edit skill instructions, references, scripts,
templates, and agent metadata there.

The maintainer tool must not contain copies or snapshots of those packages. It
reads canonical skills directly and generates only resources that must be
duplicated between independently published skills.

## Shared rules

`skills/specspine-grow/references/` owns the canonical copies of:

- `spec-format.md`;
- `spec-semantics.md`;
- `context-handoff.md`.

The generator synchronizes those files into `specspine-map` and
`specspine-doctor`. These build-time copies keep every published skill
independently installable without introducing another authoring source or a
runtime companion dependency.

Selecting `--skill specspine-grow` synchronizes both consumers. Selecting a
consumer synchronizes only that consumer. Run the full generator before a
release.

## Project adaptation boundary

Resource generation resolves framework-maintainer duplication. It cannot know
a consumer project's agent instructions, SpecSpine root, SDD workflow, paths,
or naming rules.

`specspine-connect` may generate only:

- one small persistent discovery block;
- one compact project binding when a downstream SDD workflow exists.

It must not generate another project-local skill. Generic integrations need
only the discovery block.

## Safety properties

- Use deterministic byte copying; never use an LLM rewrite.
- Write files through temporary siblings and atomic replacement.
- Make `--check` read-only and return a non-zero exit code for drift.
- Never create canonical skill instructions from files under `tools/`.
- Never persist full skill copies under `tools/`.

## Required gates

Before publishing:

1. edit canonical files under `skills/`;
2. synchronize shared resources;
3. run generation in `--check` mode;
4. validate every canonical skill with an available native validator;
5. run unit tests and the eval-manifest audit;
6. run deterministic scripts on representative valid and invalid fixtures;
7. inspect the generated diff for unintended prompt growth;
8. record the release version through the repository's release mechanism.

Generation and testing do not authorize external publishing.

The generator enforces maximum word counts for the always-loaded bootstrap,
conditional project binding, and latency-sensitive `connect` and `doctor` skill
bodies. Change a budget only with an explicit architectural reason and a before
and after runtime-cost comparison.
