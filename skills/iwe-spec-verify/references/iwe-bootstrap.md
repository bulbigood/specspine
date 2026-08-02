# IWE bootstrap protocol

Run this preflight before any Specspine read or write operation.

## Path resolution

Resolve the Specspine library path in this order:

1. the `library.path` in an existing `.iwe/config.toml`;
2. an explicit path requested by the operator when initializing IWE;
3. `docs/specs` as the fallback for a new IWE workspace.

After resolution, use IWE commands and the configured library path. Do not
construct document paths independently. The `docs/specs` fallback keeps a new
workspace from indexing every Markdown file below `docs`.

## Preflight

1. Locate the workspace root and check for `.iwe/config.toml`.
2. If it exists, read `library.path`, accept it as the workspace's configured
   scope, and continue with step 5.
3. If it does not exist, choose the operator's explicitly requested library
   path or fall back to `docs/specs`. Inspect the proposed configuration first,
   substituting the resolved path for `<library-path>`:

   ```bash
   iwe init --dry-run --json --library <library-path>
   ```

   If the report does not expose a destructive or ambiguous conflict, initialize
   the workspace:

   ```bash
   iwe init --auto --library <library-path>
   ```

4. Read the generated `.iwe/config.toml` and use its `library.path` as the
   resolved scope.
5. Ensure the `specification` template and schema settings from the Specspine
   preset are present. Merge missing settings; never replace an existing config
   wholesale.
6. If the resolved library directory already exists, preserve its name and
   contents. Do not run `iwe normalize` as part of bootstrap.
7. Run `iwe schema validate` before the requested operation. Report existing
   validation failures separately from failures introduced by the operation.

## Explicit path conflicts

An existing `library.path` that differs from `docs/specs` is valid and must not
be treated as a conflict. Use it as configured.

If the operator explicitly requests a different path while `.iwe/config.toml`
already defines `library.path`, stop before reading or writing specifications.
Do not silently change the existing path: doing so would remove the user's
current library from IWE's scope. Ask the operator to choose explicitly between:

- migrating the existing IWE library to the explicitly requested path;
- using the existing configured IWE library for Specspine;
- configuring a separate nested IWE project at the explicitly requested path.

Do not create a nested IWE project without explicit approval. When approved,
initialize it from the requested directory with a library path of `""` and run
all Specspine IWE commands with that directory as the working directory.

## Safety properties

- Never index all of `docs` merely to reach the `docs/specs` fallback.
- Never rename an existing library directory for a trial or installation.
- Never overwrite an existing `.iwe/config.toml`.
- Never move an existing IWE library without explicit approval.
- Use the configured IWE library path after preflight; do not construct document
  paths independently in later workflow steps.
