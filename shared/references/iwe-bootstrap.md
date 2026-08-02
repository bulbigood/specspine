# IWE bootstrap protocol

Use this protocol only when the workspace is not already ready for Specspine.
The bundled setup assets are in [`../assets/iwe`](../assets/iwe).

## Discover the target

1. Run the bundled [`iwe-readiness.sh`](../scripts/iwe-readiness.sh) from the
   task's working directory. Resolve the linked script path relative to this
   protocol, not relative to the workspace. It checks `iwe` and hidden
   `.iwe/config.toml` files without
   relying on `rg --files`. Use its nearest ancestor config when present. If
   the task explicitly spans a monorepo, run it once with `--descendants` to
   list package-local candidates.
2. If the task spans several packages or more than one IWE root is plausible,
   ask the operator which directory is the project root before changing
   configuration. Ask once: the selected `.iwe/config.toml` persists the
   decision for later runs.
3. If a single root is clear, do not ask about it.

After the operator selects a root, run every IWE command with that root as the
working directory. Do not run IWE from the ambiguous ancestor. Continue the
requested operation without asking for the root again in that task. Before
changing directory, resolve the bundled config and schema links to absolute
paths so they remain accessible from the selected package.

## Ensure IWE is available

Check whether `iwe` is on `PATH` before reading other IWE references or help.
If it is absent, stop discovery and ask one combined question that explicitly:

1. states that Specspine requires the latest IWE CLI;
2. offers to install it with the environment's supported package mechanism;
3. asks where specifications should live and presents `docs/specs` as the
   default, even when that directory already exists.

Do not infer approval from an existing directory. Do not install software,
create configuration, or edit documents until the operator answers both the
installation and directory questions.

After installation, use targeted `iwe <command> --help` only when a command or
option is rejected or its exact syntax remains unknown. Use `iwe --help` only
when the relevant command itself is unknown. Do not preload help screens or
guess version-specific syntax.

## Resolve the library path

Resolve the path in this order:

1. `library.path` from an existing `.iwe/config.toml`;
2. the path explicitly selected by the operator for a new IWE project;
3. `docs/specs` as the fallback for a new project.

An existing path other than `docs/specs` is valid. Use it unless the operator
explicitly requests a different path. If those two paths conflict, ask whether
to keep the existing scope, migrate it, or create a separate nested IWE
project. Never change or move an existing library without explicit approval.
Do not compare an existing `library.path` with the bundled fallback as part of
the template/schema collision check; a path difference alone never triggers
bootstrap.

## Initialize or repair configuration

When `.iwe/config.toml` and `.iwe/` are both absent, preview initialization and
then initialize with the resolved library path:

```sh
iwe init --dry-run --json --library <resolved-path>
iwe init --auto --library <resolved-path>
```

If either invocation is rejected, consult `iwe init --help` once and adapt to
the installed latest version.

When `.iwe/` exists without `config.toml`, preserve everything already inside
it. Do not call `iwe init`, delete the directory, or overwrite other files.
Create `config.toml` from the bundled
[`config.toml`](../assets/iwe/config.toml), changing only `library.path` to the
resolved path.

For an existing config, compare its complete `[templates.specification]` and
`[schemas.specification]` tables with the bundled config before editing any
document. Also compare an existing `.iwe/schemas/specification.yaml` with the
bundled schema. The scoped binding documented below is also compatible when the
library contains unrelated notes. Any other same-named table or schema with
different content is a collision, including a different `key_template`,
`document_template`, `match`, or schema body. Report the exact difference and
ask whether to keep or replace it. While waiting, leave the entire workspace
unchanged.

If there is no collision, merge only missing Specspine settings from the
bundled config. Never replace the file wholesale or overwrite same-named
templates, schemas, actions, or user formatting settings.

Bundled asset directories may themselves be symbolic links. Inspect the exact
linked `config.toml` and `schemas/specification.yaml` paths with `test -f`,
`cmp`, or a direct read; `find <symlink-directory> -type f` can return nothing
and is not evidence that the assets are absent.

Copy the bundled
[`schemas/specification.yaml`](../assets/iwe/schemas/specification.yaml) to
`.iwe/schemas/specification.yaml` when it is absent, creating `.iwe/schemas/`
first when necessary. Never overwrite a different existing schema without
approval.

Before editing a specification, verify all three bootstrap postconditions:
`.iwe/config.toml` contains `[templates.specification]` and
`[schemas.specification]`, and `.iwe/schemas/specification.yaml` exists. A
successful `iwe schema validate` is not sufficient when no schema is bound.

## Bind the schema safely

The default preset treats the resolved library as a dedicated Specspine
library: `key_template = "{{slug}}"` and schema `match = "**"`.

Before adding that binding to a non-empty existing IWE library, inspect its
documents. Treat the library as non-empty when `iwe find -f keys` returns any
key, even if no Specspine document exists yet. A document whose frontmatter
contains `specspine: 5` is already a Specspine document even when the template
or schema has not been installed yet. If every document declares that field,
the dedicated
binding is safe. If any existing document does not, preserve it and scope new
Specspine documents below a `specspine/` key prefix:

```toml
[templates.specification]
key_template = "specspine/{{slug}}"

[schemas.specification]
match = "specspine/**"
```

This keeps unrelated existing notes indexed by IWE without forcing them to
validate as Specspine. Do not move or rename existing documents merely to test
the skills.

## Validate

Do not run `iwe normalize` during bootstrap. Run `iwe schema validate` before
the requested operation and distinguish pre-existing failures from failures
introduced by the operation. Use the resolved IWE library thereafter; do not
construct document paths independently.
