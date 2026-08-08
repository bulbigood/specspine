---
name: iwe-spec-setup
description: Configure an IWE workspace for Specspine using the bundled template and schema while preserving unrelated settings. Use only when the user explicitly asks to initialize, set up, bootstrap, or repair the initial Specspine workspace configuration.
---

# IWE Spec Setup

Define the desired Specspine workspace state and delegate all IWE work.

Find an available skill whose description covers IWE installation, projects,
libraries, configuration, and document operations. Read it and delegate every
interaction with IWE to it, including environment discovery, installation
guidance, project initialization, configuration changes, and validation. State
the result needed; do not prescribe commands, package managers, URLs, flags,
syntax, or compatibility handling. If no applicable IWE skill is available,
report the missing capability and stop. Do not install another agent skill.

The canonical setup assets are bundled at `assets/iwe/`:

- `config.toml` supplies the Specspine template and schema-binding tables;
- `schemas/specification.yaml` is the executable Specspine document schema.

Reuse answers already supplied by the user. Ask only for unresolved choices or
for confirmation required before a consequential change; do not force a
multi-turn sequence when all safe values are already explicit.

## Desired outcome

1. Ask the selected IWE skill to identify the intended workspace, any existing
   IWE project, its Markdown library, and whether the current Specspine setup is
   complete. When several projects plausibly own the task, ask the user to choose
   before any write.
2. If IWE itself is unavailable, ask that skill for current compatible
   installation options. Present its recommendation and obtain approval before
   any installation outside the workspace.
3. Reuse an existing library path unless the user asks to change it. For a new
   workspace, obtain a contained Markdown-library directory; offer `docs` only
   when the user has not supplied a preference.
4. Obtain a Specspine directory that is a strict descendant of the resolved IWE
   library. Offer `<library>/specs` only when no preference was supplied. Reject
   traversal, symlink escape, the library root itself, and paths outside the
   library.
5. Derive the IWE key prefix from the Specspine directory relative to the
   library. Require the template key `<prefix>/{{slug}}` and schema match
   `<prefix>/**`.
6. Present the resolved workspace, library, Specspine directory, key template,
   and schema match. Obtain confirmation before writes unless the user already
   made all of those exact values explicit.
7. Give the selected IWE skill the bundled assets and desired end state. Require
   it to preserve unrelated configuration, add only missing Specspine state,
   detect differing Specspine tables or schema as conflicts, and obtain approval
   before replacing a conflict. Do not partially apply an unresolved conflict.
8. Require the selected IWE skill to validate the final workspace without
   rewriting existing documents to hide validation failures.

Report the IWE version, resolved workspace and library, Specspine directory and
key prefix, changed and unchanged files, conflicts, and validation result.

Keep the operation idempotent. Do not create a sample specification, normalize
the Markdown library, move existing documents, or repair editor integration
unless the user explicitly requests that separate work.
