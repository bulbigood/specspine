# IWE bootstrap protocol

Use this protocol only when the workspace is not already ready for Specspine.
The bundled setup assets are in [`../assets/iwe`](../assets/iwe).

## Discover the target

1. Starting at the task's working directory, look for `.iwe/config.toml` in
   that directory and its ancestors. Use the nearest one whose scope contains
   the task.
2. If the task spans several packages or more than one IWE root is plausible,
   ask the operator which directory is the project root before changing
   configuration. Ask once: the selected `.iwe/config.toml` persists the
   decision for later runs.
3. If a single root is clear, do not ask about it.

## Ensure IWE is available

Check whether `iwe` is on `PATH`. If it is absent, explain that Specspine needs
the latest IWE CLI and offer to install it using the environment's supported
package mechanism. In the same interaction, ask where specifications should
live and present `docs/specs` as the default. Do not install software or create
configuration until the operator approves.

After installation, use `iwe --help` and targeted `iwe <command> --help` output
whenever a command or option is rejected. Do not guess version-specific syntax.

## Resolve the library path

Resolve the path in this order:

1. `library.path` from an existing `.iwe/config.toml`;
2. the path explicitly selected by the operator for a new IWE project;
3. `docs/specs` as the fallback for a new project.

An existing path other than `docs/specs` is valid. Use it unless the operator
explicitly requests a different path. If those two paths conflict, ask whether
to keep the existing scope, migrate it, or create a separate nested IWE
project. Never change or move an existing library without explicit approval.

## Initialize or repair configuration

When `.iwe/config.toml` and `.iwe/` are both absent, preview initialization and
then initialize with the resolved library path. Prefer `iwe init --dry-run`
before `iwe init --auto`; confirm exact options through `iwe init --help` if
needed.

When `.iwe/` exists without `config.toml`, preserve everything already inside
it. Do not call `iwe init`, delete the directory, or overwrite other files.
Create `config.toml` from the bundled
[`config.toml`](../assets/iwe/config.toml), changing only `library.path` to the
resolved path.

For an existing config, merge only missing Specspine settings from the bundled
config. Never replace the file wholesale or overwrite same-named templates,
schemas, actions, or user formatting settings. If a same-named setting has
different content, report the collision and ask before changing it.

Copy the bundled
[`schemas/specification.yaml`](../assets/iwe/schemas/specification.yaml) to
`.iwe/schemas/specification.yaml` when it is absent. Never overwrite a
different existing schema without approval.

## Bind the schema safely

The default preset treats the resolved library as a dedicated Specspine
library: `key_template = "{{slug}}"` and schema `match = "**"`.

Before adding that binding to a non-empty existing IWE library, inspect its
documents. If every document already declares `specspine: 5`, the dedicated
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
