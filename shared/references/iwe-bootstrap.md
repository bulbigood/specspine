# IWE project setup

Read this reference only when the current IWE project is missing the Specspine
template, schema binding, or schema file, or when one of them conflicts with the
bundled assets.

## Preconditions

Specspine expects the operator to install and initialize IWE. If `iwe` is not
available, stop and point to the official installation guide:

<https://iwe.md/docs/getting-started/installation/>

If the workspace has no `.iwe/config.toml`, stop and ask the operator to run
this from the intended workspace root:

```bash
iwe init --auto --library docs
```

Do not install software or initialize an IWE project on the operator's behalf.
If several IWE roots plausibly own the task, ask which root to use before
changing anything. Run subsequent IWE operations from the selected root.

## Install the Specspine binding

Treat the existing `library.path` as authoritative. Do not move documents or
replace the IWE configuration to match the bundled default.

Compare the existing `[templates.specification]` and
`[schemas.specification]` tables with the bundled `assets/iwe/config.toml`, and
compare `.iwe/schemas/specification.yaml` with the bundled schema.

The canonical binding is scoped within the IWE library:

```toml
[templates.specification]
key_template = "specs/{{slug}}"

[schemas.specification]
match = "specs/**"
```

This lets ordinary Markdown documents and Specspine owners coexist in one IWE
graph. Do not widen the schema match to the entire library.

- If a table or schema file is missing, add only that missing Specspine data.
- If a same-named table or schema differs, report the exact difference and ask
  whether to keep or replace it. Leave the workspace unchanged while waiting.
- Preserve all unrelated IWE settings, templates, schemas, actions, and files.
- Never copy the bundled config over an existing `.iwe/config.toml` wholesale.

After installing the binding, verify that both tables and the schema file exist,
then run `iwe schema validate`. A successful command with no matching schema is
not proof that Specspine was installed.

Do not add bootstrap scripts, generated manifests, indexes, or a second parser.
