---
name: iwe-spec-setup
description: Guide a user through installing IWE, choosing the IWE Markdown library, choosing a contained Specspine directory, and configuring the workspace without replacing unrelated settings. Use only when the user explicitly asks to initialize, set up, bootstrap, or repair the initial Specspine workspace configuration.
---

# IWE Spec Setup

Configure the workspace through a linear conversation, then leave ongoing
specification work to the workflow skills. Use the installed official
`iwe-memory-system` skill for IWE project discovery and commands; read it before
continuing. If it is unavailable, stop and point the user to the repository
README instead of installing it.

The canonical setup assets are bundled at `assets/iwe/` relative to this file:

- `config.toml` contains a complete reference configuration. Use only its
  `[templates.specification]` and `[schemas.specification]` tables as the source
  template, adapting their key prefix to the directory chosen by the user.
- `schemas/specification.yaml` is the executable Specspine document schema.

Do not install other agent skills, execute an unreviewed installer, or use a
bundled setup script. This skill contains no scripts.

## Workflow

Complete each decision before advancing to the next one. Do not collect all
answers in advance or silently select defaults.

### 1. Ensure IWE is installed

1. Run `iwe --version`.
2. If IWE is unavailable, read the current installation section in the official
   IWE GitHub README at https://github.com/iwe-org/iwe and the official guide at
   https://iwe.md/docs/getting-started/installation/.
3. Detect the user's operating system and available package managers. Present
   only currently documented, compatible installation methods, including each
   method's prerequisite and exact command. Recommend the simplest compatible
   official method, but ask the user which one to use.
4. After the user chooses, show the exact command and obtain approval before
   running it. Installation may change software outside the workspace.
5. Run only the approved official command, then verify `iwe --version`. If it
   fails, stop with the command output; do not switch methods automatically.

### 2. Resolve the workspace

1. Resolve the intended workspace root. Prefer an existing ancestor containing
   `.iwe/config.toml`. If multiple IWE roots plausibly own the task, ask the
   user to select one before writing anything.
2. If `.iwe/` exists without `config.toml`, stop and report the incomplete
   initialization. Do not delete or replace the directory.
3. Treat the directory containing an existing `.iwe/` as the IWE workspace
   root. For an uninitialized project, propose the current working directory
   and ask the user to confirm it or provide another root. Do not initialize
   until the root is explicit.
4. For an existing workspace, check whether its current library path,
   Specspine template and schema binding, canonical schema file, and
   specification directory already form a complete valid setup. If they do,
   run `iwe schema validate`, leave every file unchanged, and report the
   existing setup immediately. Do not ask the user to reconfirm values that do
   not need to change. Continue with the decisions below only when setup is
   incomplete, conflicting, or the user explicitly asks to change it.

### 3. Choose and initialize the IWE library

1. If `.iwe/config.toml` exists, read its current `library.path`, explain what it
   resolves to, and ask whether to keep it. If the user wants to change it, or
   if the workspace is new, ask which directory inside the workspace should
   contain all Markdown that IWE manages. Explain that this becomes
   `library.path`, relative to the workspace root. Offer `docs` as the default
   for a new workspace and explain that the workspace root itself is represented
   by an empty path.
2. Normalize the answer against the workspace root. Reject absolute or relative
   paths that escape it, including `..` traversal and symlink resolution outside
   the root. For a path that does not exist yet, resolve its nearest existing
   parent before checking containment. Store the result as a normalized relative
   path without `.` or `..` segments. Ask again instead of rewriting an unsafe
   path.
3. If `.iwe/config.toml` does not exist, run
   `iwe init --auto --library <chosen-relative-path>` from the workspace root.
   Pass an empty argument (`--library ""`) when the user chooses the workspace
   root itself.
4. Before changing an existing `library.path`, explain that existing Markdown
   outside the new library will no longer be managed by IWE. Change only
   `[library].path` after explicit confirmation; do not move documents
   automatically.
5. Read the resulting `.iwe/config.toml` and resolve the absolute library root.

### 4. Choose the Specspine directory

1. Ask where Specspine specifications should live. Accept an absolute path or a
   path relative to the workspace, then normalize it. Offer
   `<library.path>/specs` as the default.
2. Require the normalized directory to be a strict descendant of the resolved
   IWE library root. Being merely inside the workspace is insufficient because
   IWE cannot assign document keys to files outside `library.path`. Reject the
   library root itself so the Specspine schema does not apply to every ordinary
   IWE document.
3. Reject traversal or symlink resolution outside the library. For a directory
   that does not exist yet, resolve its nearest existing parent before checking
   containment.
4. Derive the IWE key prefix as the directory path relative to the library,
   using `/` separators. For example, workspace `library.path = "docs"` and
   directory `docs/architecture/specs` produce the key prefix
   `architecture/specs`.
5. Show the resolved library root, Specspine directory, key template
   `<prefix>/{{slug}}`, and schema match `<prefix>/**`; ask the user to confirm
   before writing.

### 5. Configure Specspine

1. Read the bundled configuration and schema. Adapt only these two values in the
   bundled Specspine tables:
   - `[templates.specification].key_template = "<prefix>/{{slug}}"`
   - `[schemas.specification].match = "<prefix>/**"`
2. Preflight all destinations before changing them:
   - Missing Specspine tables and schema may be added.
   - Identical Specspine tables or schema are already configured and require no
     write.
   - A differing `[templates.specification]`, `[schemas.specification]`, or
     `.iwe/schemas/specification.yaml` is a conflict. Show the difference and
     obtain explicit user approval before replacing it. Do not partially apply
     the remaining setup while a conflict is unresolved.
3. Append only the adapted `[templates.specification]` and
   `[schemas.specification]` tables to `.iwe/config.toml`. Never replace the
   generated configuration or unrelated settings.
4. Create `.iwe/schemas/` if needed and copy the bundled
   `schemas/specification.yaml` byte-for-byte to
   `.iwe/schemas/specification.yaml`.
5. Create the confirmed Specspine directory if it does not exist.
6. Run `iwe schema validate` from the workspace root. Do not edit existing
   documents merely to make initial setup validation pass; report their errors
   separately.
7. Report the IWE version, resolved workspace and library roots, Specspine
   directory and key prefix, changed and unchanged files, any conflicts, and the
   validation result.

## Guardrails

- Make the operation idempotent: a second run against the same version must
  produce no changes.
- Preserve comments and table ordering outside the two Specspine tables.
- Do not run `iwe normalize`; setup must not rewrite the Markdown library.
- Do not create a sample specification unless the user asks for one.
- Do not repair workflow-skill installation or editor integration.
