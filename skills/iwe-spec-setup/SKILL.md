---
name: iwe-spec-setup
description: Configure an IWE workspace for Specspine using the bundled template and schema while preserving unrelated settings. Use only when the user explicitly asks to initialize, set up, bootstrap, or repair the initial Specspine workspace configuration.
---

# IWE Spec Setup

Define the desired Specspine workspace state and delegate all IWE work.

First ensure that an agent skill whose declared capability covers IWE
installation, projects, libraries, configuration, and document operations is
available. Use <https://github.com/iwe-org/skills> as the authoritative catalog
and installation source. Inspect its available skills and compare them with any
already installed candidate before installing another one; do not require a
particular skill name.

Determine the installed IWE CLI version when IWE is present. For each candidate,
read the supported IWE CLI version or range from its name or metadata; treat the
repository's version metadata, including `metadata.version`, as its declared CLI
compatibility. Select the candidate that best matches the installed CLI version
and covers every delegated IWE capability required here. Prefer an exact version
match, then an explicitly compatible range, then the repository's current
recommended compatible candidate. Never guess compatibility from command
examples. If IWE is absent, select the repository's current recommended skill
and let it guide installation of the IWE CLI version it supports. If no candidate
declares a compatible version, report the mismatch and obtain approval before
changing the installed CLI version.

If installation is needed, use an available skill-installation capability.
Before installing, present the selected skill, declared CLI compatibility,
source, and installation target and obtain fresh explicit approval. If no
installation capability is available, or no suitable candidate can be
established, report the missing capability and stop. After installation, use the
new skill only if the agent runtime makes it available in the current session.
Otherwise report that a skill reload or new session is required and stop; resume
setup after the skill is visible instead of operating IWE directly.

Read the selected IWE skill and delegate every interaction with IWE to it,
including environment discovery, IWE installation guidance, project
initialization, configuration changes, and validation. State the result needed;
do not prescribe commands, package managers, URLs, flags, syntax, or
compatibility handling.

The canonical setup assets are bundled at `assets/iwe/`:

- `config.toml` is a merge source for the Specspine template and schema-binding
  tables, not a replacement for the workspace configuration;
- `schemas/specification.yaml` is the executable Specspine document schema and
  must be installed at `<workspace>/.iwe/schemas/specification.yaml`.

Reuse answers already supplied by the user. Ask only for unresolved choices or
for confirmation required before a consequential change; do not force a
multi-turn sequence when all safe values are already explicit.

## Desired outcome

1. Establish the most suitable version-compatible IWE skill from the official
   catalog using the bootstrap rule above. If IWE is already installed, do not
   reinstall or replace it merely because the skill had to be added.
2. Ask the selected IWE skill to identify the intended workspace, any existing
   IWE project, its Markdown library, and whether the current Specspine setup is
   complete. When several projects plausibly own the task, ask the user to choose
   before any write.
3. If IWE itself is unavailable, ask that skill for current compatible
   installation options. Present its recommendation and obtain approval before
   any installation outside the workspace.
4. Reuse an existing library path unless the user asks to change it. For a new
   workspace, obtain a contained Markdown-library directory; offer `docs` only
   when the user has not supplied a preference.
5. Obtain a Specspine directory that is a strict descendant of the resolved IWE
   library. Offer `<library>/specs` only when no preference was supplied. Reject
   traversal, symlink escape, the library root itself, and paths outside the
   library.
6. Derive the IWE key prefix from the Specspine directory relative to the
   library. Require the template key `<prefix>/{{slug}}` and schema match
   `<prefix>/**`.
7. Present the resolved workspace, library, Specspine directory, key template,
   and schema match. Obtain confirmation before writes unless the user already
   made all of those exact values explicit.
8. For a new project, require the selected IWE skill to initialize the IWE
   project with the resolved library before integrating Specspine. For an
   existing project, retain its `<workspace>/.iwe/config.toml` as the base.
9. Give the selected IWE skill the bundled assets and require a field-level
   merge into `<workspace>/.iwe/config.toml`: add or reconcile only
   `[templates.specification]` and `[schemas.specification]`, using the resolved
   prefix for `key_template` and `match`. Never copy the bundled file wholesale.
   Treat its top-level `version` and `[library]` values only as defaults for a
   new IWE project; never overwrite those or any unrelated existing tables,
   fields, comments, actions, commands, formatting, or library settings.
10. Require the selected IWE skill to create the confirmed Specspine directory
   and install the bundled schema byte-for-byte at
   `<workspace>/.iwe/schemas/specification.yaml`. An identical existing table or
   schema is a no-op. Any differing Specspine table or destination schema is a
   conflict: show the difference and obtain approval before replacing a conflict.
   Preflight all conflicts before writing and do not partially apply an
   unresolved integration.
11. Require the selected IWE skill to validate the complete final workspace,
   including configuration, schema binding, schema file, and existing
   Specspine documents, without rewriting documents to hide validation failures.

Report the IWE version, resolved workspace and library, Specspine directory and
key prefix, changed and unchanged files, conflicts, and validation result.

Keep the operation idempotent. Do not create a sample specification, normalize
the Markdown library, move existing documents, or repair editor integration
unless the user explicitly requests that separate work.
